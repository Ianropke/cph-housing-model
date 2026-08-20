#!/usr/bin/env python3
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, "../server")
from cph_housing_server import run_forecast_ensemble, check_early_warnings

class TestPipelineErrors(unittest.TestCase):
    def test_run_forecast_ensemble_unknown_city(self):
        result = run_forecast_ensemble("unknown_city")
        self.assertIn("error", result)
        self.assertIn("Unknown segment", result["error"])

    @patch("dst_macro.fetch_dst_macro_data")
    def test_check_early_warnings_unknown_city(self, mock_fetch):
        # We also want to mock the fetch so it doesn't fail due to API
        mock_fetch.return_value = {"unemployment_rate": 0.035, "rent_index": 120.0, "disposable_income_cph": 400000.0, "disposable_income_frb": 400000.0, "wage_growth": 0.032}
        
        result = check_early_warnings("unknown_city")
        self.assertIn("error", result)
        self.assertIn("Unknown segment", result["error"])

if __name__ == "__main__":
    unittest.main()
