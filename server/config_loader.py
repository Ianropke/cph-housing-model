"""
Copenhagen Housing Market — Canonical Configuration Loader
Single source of truth for scenarios, EWI thresholds, and model parameters.
Loads directly from config/scenarios.yaml to guarantee zero configuration drift.
"""

import os
import yaml
from pathlib import Path

# Path resolution to project root
BASE_DIR = Path(__file__).resolve().parent.parent
SCENARIOS_YAML_PATH = os.path.join(BASE_DIR, "config", "scenarios.yaml")

_scenarios_cache = None


def load_scenarios(force_reload=False):
    """
    Loads and returns the canonical scenarios configuration dictionary from config/scenarios.yaml.
    Caches result in memory unless force_reload=True.
    Populates backward-compatible properties so all model engines and tests work seamlessly.
    """
    global _scenarios_cache
    if _scenarios_cache is not None and not force_reload:
        return _scenarios_cache

    if not os.path.exists(SCENARIOS_YAML_PATH):
        raise FileNotFoundError(f"Canonical scenarios file not found at: {SCENARIOS_YAML_PATH}")

    with open(SCENARIOS_YAML_PATH, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    # Valid scenario keys only
    valid_keys = ["baseline", "min_risk", "max_risk"]
    scenarios = {}

    for key in valid_keys:
        if key in data and isinstance(data[key], dict):
            s = dict(data[key])
            drivers = s.get("drivers", {})
            cc = drivers.get("credit_conditions", {})
            pp = drivers.get("purchasing_power", {})
            exp = s.get("expected_appreciation_yoy", {})

            # Populate legacy compatibility properties directly on the dictionary
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

    _scenarios_cache = scenarios
    return scenarios


def get_scenario_user_cost_params():
    """
    Returns user cost calculation parameters for baseline, min_risk, and max_risk scenarios.
    Maps canonical YAML driver fields into the exact parameters required by user_cost_model.
    """
    scenarios = load_scenarios()
    
    user_cost_params = {}
    for name, s in scenarios.items():
        drivers = s.get("drivers", {})
        cc = drivers.get("credit_conditions", {})
        pp = drivers.get("purchasing_power", {})
        exp = s.get("expected_appreciation_yoy", {})

        user_cost_params[name] = {
            "label": s.get("label", name.capitalize()),
            "probability_weight": s.get("probability_weight", 0.33),
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
            "description": s.get("description", "").strip()
        }

    return user_cost_params


def get_scenario_rates_and_appreciation(scenario, horizon_key):
    """
    Extracts mortgage rate, expected appreciation, and implied rate for a specific horizon key (6m, 12m, 24m)
    from a scenario dictionary, supporting both legacy flat dicts and canonical YAML driver structures.
    """
    if "mortgage_rate" in scenario and isinstance(scenario["mortgage_rate"], dict):
        rate = scenario["mortgage_rate"].get(horizon_key, scenario["mortgage_rate"].get("12m", 0.037))
        appreciation = scenario["expected_appreciation"].get(horizon_key, scenario["expected_appreciation"].get("12m", 0.035))
        implied_rate = scenario["mortgage_rate"].get("6m", 0.039)
    else:
        drivers = scenario.get("drivers", {})
        cc = drivers.get("credit_conditions", {})
        exp = scenario.get("expected_appreciation_yoy", {})

        hk_num = horizon_key.replace("m", "")
        if hk_num == "6":
            rate = cc.get("fixed_30y_mortgage_rate_6m", cc.get("fixed_30y_mortgage_rate_current", 0.04))
            appreciation = exp.get("month_6", exp.get("year_1", 0.035) / 2.0)
        elif hk_num == "24":
            rate = cc.get("fixed_30y_mortgage_rate_24m", 0.035)
            appreciation = exp.get("year_2", 0.06)
        else:  # 12m default
            rate = cc.get("fixed_30y_mortgage_rate_12m", 0.037)
            appreciation = exp.get("year_1", 0.035)

        implied_rate = cc.get("fixed_30y_mortgage_rate_6m", cc.get("fixed_30y_mortgage_rate_current", 0.04))

    return rate, appreciation, implied_rate


if __name__ == "__main__":
    print("Successfully loaded canonical scenarios:")
    scenarios = load_scenarios(force_reload=True)
    for name, s in scenarios.items():
        print(f"  • {name}: {s.get('label')} (Weight: {s.get('probability_weight')})")
