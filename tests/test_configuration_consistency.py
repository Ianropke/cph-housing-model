"""
Unit test suite verifying canonical configuration consistency.
Ensures config/scenarios.yaml is the single source of truth across server, pipeline, and tests.
"""

import unittest
import os
import sys

# Ensure server module is on PYTHONPATH
server_dir = os.path.join(os.path.dirname(__file__), "..", "server")
if server_dir not in sys.path:
    sys.path.insert(0, server_dir)

from config_loader import load_scenarios, get_scenario_user_cost_params
from cph_housing_server import SCENARIOS


class TestConfigurationConsistency(unittest.TestCase):
    def test_canonical_scenarios_exist(self):
        """Verifies that all three primary scenarios exist in scenarios.yaml."""
        scenarios = load_scenarios(force_reload=True)
        self.assertIn("baseline", scenarios)
        self.assertIn("min_risk", scenarios)
        self.assertIn("max_risk", scenarios)

    def test_probability_weights_sum_to_one(self):
        """Verifies that scenario probability weights sum to exactly 1.0."""
        scenarios = load_scenarios()
        total_weight = sum(
            scenarios[key].get("probability_weight", 0)
            for key in ["baseline", "min_risk", "max_risk"]
        )
        self.assertAlmostEqual(total_weight, 1.0, places=4, msg="Scenario probability weights must sum to 1.0")

    def test_server_scenarios_match_canonical_loader(self):
        """Verifies that cph_housing_server.SCENARIOS is strictly aligned with config_loader."""
        scenarios_from_loader = load_scenarios()
        for key in ["baseline", "min_risk", "max_risk"]:
            self.assertIn(key, SCENARIOS, f"Key '{key}' missing from cph_housing_server.SCENARIOS")
            self.assertEqual(
                SCENARIOS[key].get("probability_weight"),
                scenarios_from_loader[key].get("probability_weight"),
                f"Probability weight mismatch for scenario '{key}'"
            )

    def test_user_cost_params_structure(self):
        """Verifies that get_scenario_user_cost_params returns valid parameters."""
        params = get_scenario_user_cost_params()
        for key in ["baseline", "min_risk", "max_risk"]:
            self.assertIn(key, params)
            p = params[key]
            self.assertIn("mortgage_rate", p)
            self.assertIn("ecb_deposit_rate", p)
            self.assertIn("wage_growth", p)
            self.assertIn("12m", p["mortgage_rate"])
            self.assertGreater(p["mortgage_rate"]["12m"], 0.0)


if __name__ == "__main__":
    unittest.main()
