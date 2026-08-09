"""
Copenhagen Housing Market — Canonical Configuration Loader
Single source of truth for scenarios, EWI thresholds, and model parameters.
Loads directly from config/scenarios.yaml to guarantee zero configuration drift.
"""

import yaml
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
SCENARIOS_YAML_PATH = BASE_DIR / "config" / "scenarios.yaml"

_scenarios_cache = None
VALID_SCENARIO_KEYS = ("baseline", "min_risk", "max_risk")


def _validate_scenario_weights(scenarios: dict) -> None:
    """Validate ensemble weights before exposing configuration to model code."""
    missing = [k for k in VALID_SCENARIO_KEYS if k not in scenarios]
    if missing:
        raise ValueError(f"Missing canonical scenarios: {', '.join(missing)}")

    weights = []
    for key in VALID_SCENARIO_KEYS:
        value = scenarios[key].get("ensemble_weight", scenarios[key].get("probability_weight"))
        if value is None:
            raise ValueError(f"Scenario '{key}' has no ensemble_weight")
        try:
            value = float(value)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Scenario '{key}' ensemble_weight must be numeric") from exc
        if not 0.0 <= value <= 1.0:
            raise ValueError(f"Scenario '{key}' ensemble_weight must be between 0 and 1")
        weights.append(value)

    total = sum(weights)
    if abs(total - 1.0) > 1e-6:
        raise ValueError(f"Scenario ensemble weights must sum to 1.0; got {total:.8f}")


def load_scenarios(force_reload=False):
    """
    Load the canonical scenario configuration.

    ``ensemble_weight`` is authoritative. ``probability_weight`` remains only
    as a backwards-compatible alias for older model consumers and must not be
    interpreted as a calibrated probability.
    """
    global _scenarios_cache
    if _scenarios_cache is not None and not force_reload:
        return _scenarios_cache

    if not SCENARIOS_YAML_PATH.exists():
        raise FileNotFoundError(f"Canonical scenarios file not found at: {SCENARIOS_YAML_PATH}")

    with SCENARIOS_YAML_PATH.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    scenarios = {}
    for key in VALID_SCENARIO_KEYS:
        if key not in data or not isinstance(data[key], dict):
            continue

        s = dict(data[key])
        ensemble_weight = s.get("ensemble_weight", s.get("probability_weight"))
        if ensemble_weight is None:
            raise ValueError(f"Scenario '{key}' must define ensemble_weight")

        s["ensemble_weight"] = float(ensemble_weight)
        # Backward-compatible alias. New code should use ensemble_weight.
        s["probability_weight"] = s["ensemble_weight"]

        drivers = s.get("drivers", {})
        cc = drivers.get("credit_conditions", {})
        pp = drivers.get("purchasing_power", {})
        exp = s.get("expected_appreciation_yoy", {})

        s["mortgage_rate"] = {
            "6m": cc.get("fixed_30y_mortgage_rate_6m", cc.get("fixed_30y_mortgage_rate_current", 0.04)),
            "12m": cc.get("fixed_30y_mortgage_rate_12m", 0.037),
            "24m": cc.get("fixed_30y_mortgage_rate_24m", 0.035),
        }
        s["expected_appreciation"] = {
            "6m": exp.get("month_6", exp.get("year_1", 0.035) / 2.0),
            "12m": exp.get("year_1", 0.035),
            "24m": exp.get("year_2", 0.06),
        }
        s["rentefradrag"] = pp.get("rentefradrag_rate", 0.33)
        s["wage_growth"] = pp.get("nominal_wage_growth_yoy", 0.035)
        s["depreciation"] = 0.015
        s["risk_premium"] = 0.010
        scenarios[key] = s

    _validate_scenario_weights(scenarios)
    _scenarios_cache = scenarios
    return scenarios


def get_scenario_user_cost_params():
    """Return user-cost parameters derived exclusively from canonical scenarios."""
    scenarios = load_scenarios()
    user_cost_params = {}
    for name, s in scenarios.items():
        drivers = s.get("drivers", {})
        cc = drivers.get("credit_conditions", {})
        pp = drivers.get("purchasing_power", {})
        exp = s.get("expected_appreciation_yoy", {})

        user_cost_params[name] = {
            "label": s.get("label", name.capitalize()),
            "ensemble_weight": s["ensemble_weight"],
            "probability_weight": s["ensemble_weight"],  # legacy alias only
            "mortgage_rate": {
                "6m": cc.get("fixed_30y_mortgage_rate_6m", cc.get("fixed_30y_mortgage_rate_current", 0.04)),
                "12m": cc.get("fixed_30y_mortgage_rate_12m", 0.037),
                "24m": cc.get("fixed_30y_mortgage_rate_24m", 0.035),
            },
            "ecb_deposit_rate": {
                "6m": cc.get("ecb_deposit_rate_6m", 0.025),
                "12m": cc.get("ecb_deposit_rate_12m", 0.0225),
                "24m": cc.get("ecb_deposit_rate_24m", 0.02),
            },
            "wage_growth": pp.get("nominal_wage_growth_yoy", 0.035),
            "rentefradrag_rate": pp.get("rentefradrag_rate", 0.33),
            "expected_appreciation": {
                "6m": exp.get("month_6", exp.get("year_1", 0.035) / 2.0),
                "12m": exp.get("year_1", 0.035),
                "24m": exp.get("year_2", 0.06),
            },
            "description": s.get("description", "").strip(),
        }
    return user_cost_params


def get_scenario_rates_and_appreciation(scenario, horizon_key):
    """Extract mortgage rate and expected appreciation for a forecast horizon."""
    if "mortgage_rate" in scenario and isinstance(scenario["mortgage_rate"], dict):
        rate = scenario["mortgage_rate"].get(horizon_key, scenario["mortgage_rate"].get("12m", 0.037))
        appreciation = scenario["expected_appreciation"].get(horizon_key, scenario["expected_appreciation"].get("12m", 0.035))
        implied_rate = scenario["mortgage_rate"].get("6m", 0.039)
    else:
        drivers = scenario.get("drivers", {})
        cc = drivers.get("credit_conditions", {})
        exp = scenario.get("expected_appreciation_yoy", {})
        if horizon_key == "6m":
            rate = cc.get("fixed_30y_mortgage_rate_6m", cc.get("fixed_30y_mortgage_rate_current", 0.04))
            appreciation = exp.get("month_6", exp.get("year_1", 0.035) / 2.0)
        elif horizon_key == "24m":
            rate = cc.get("fixed_30y_mortgage_rate_24m", 0.035)
            appreciation = exp.get("year_2", 0.06)
        else:
            rate = cc.get("fixed_30y_mortgage_rate_12m", 0.037)
            appreciation = exp.get("year_1", 0.035)
        implied_rate = cc.get("fixed_30y_mortgage_rate_6m", cc.get("fixed_30y_mortgage_rate_current", 0.04))

    return rate, appreciation, implied_rate


if __name__ == "__main__":
    print("Successfully loaded canonical scenarios:")
    for name, s in load_scenarios(force_reload=True).items():
        print(f"  • {name}: {s.get('label')} (Ensemble weight: {s.get('ensemble_weight')})")
