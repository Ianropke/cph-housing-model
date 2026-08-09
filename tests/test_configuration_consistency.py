"""Tests for canonical scenario configuration and model semantics."""

import os
import sys
import unittest

server_dir = os.path.join(os.path.dirname(__file__), "..", "server")
if server_dir not in sys.path:
    sys.path.insert(0, server_dir)

from config_loader import load_scenarios, get_scenario_user_cost_params
from cph_housing_server import SCENARIOS


SCENARIO_KEYS = ("baseline", "min_risk", "max_risk")


class TestConfigurationConsistency(unittest.TestCase):
    def test_canonical_scenarios_exist(self):
        scenarios = load_scenarios(force_reload=True)
        for key in SCENARIO_KEYS:
            self.assertIn(key, scenarios)

    def test_ensemble_weights_sum_to_one(self):
        scenarios = load_scenarios()
        weights = [scenarios[key]["ensemble_weight"] for key in SCENARIO_KEYS]
        self.assertAlmostEqual(sum(weights), 1.0, places=6)
        for weight in weights:
            self.assertGreaterEqual(weight, 0.0)
            self.assertLessEqual(weight, 1.0)

    def test_weights_are_not_presented_as_calibrated_probabilities(self):
        """Scenario weights are ensemble weights, not empirical probabilities."""
        scenarios = load_scenarios()
        for key in SCENARIO_KEYS:
            self.assertIn("ensemble_weight", scenarios[key])
            self.assertEqual(scenarios[key]["probability_weight"], scenarios[key]["ensemble_weight"])

    def test_server_scenarios_match_canonical_loader(self):
        canonical = load_scenarios()
        for key in SCENARIO_KEYS:
            self.assertIn(key, SCENARIOS)
            self.assertAlmostEqual(
                SCENARIOS[key]["ensemble_weight"],
                canonical[key]["ensemble_weight"],
                places=8,
                msg=f"Ensemble weight mismatch for scenario '{key}'",
            )

    def test_user_cost_params_structure(self):
        params = get_scenario_user_cost_params()
        for key in SCENARIO_KEYS:
            self.assertIn(key, params)
            p = params[key]
            self.assertIn("ensemble_weight", p)
            self.assertAlmostEqual(p["ensemble_weight"], p["probability_weight"])
            self.assertIn("mortgage_rate", p)
            self.assertIn("ecb_deposit_rate", p)
            self.assertIn("wage_growth", p)
            self.assertIn("12m", p["mortgage_rate"])
            self.assertGreater(p["mortgage_rate"]["12m"], 0.0)


if __name__ == "__main__":
    unittest.main()
