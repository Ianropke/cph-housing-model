import copy
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, "server")

from cph_housing_server import (  # noqa: E402
    DST_EJ56_DATA,
    check_early_warnings,
    run_forecast_ensemble,
)


class TestLiveDataAlignment(unittest.TestCase):
    def setUp(self):
        self.live_data = copy.deepcopy(DST_EJ56_DATA)
        self.live_data["source"] = "DST EJ56 live test fixture"
        for segment in self.live_data["segments"].values():
            latest_period = sorted(segment["series"])[-1]
            segment["latest_period"] = latest_period
            segment["latest_value"] = segment["series"][latest_period]

    def test_forecast_uses_supplied_live_period_and_index(self):
        for segment_name, segment in self.live_data["segments"].items():
            latest_period = segment["latest_period"]
            live_index = segment["latest_value"] + 1.25
            segment["series"][latest_period] = live_index
            segment["latest_value"] = live_index

            result = run_forecast_ensemble(segment=segment_name, horizons=[12], dst_data=self.live_data)

            self.assertEqual(result["current_period"], latest_period)
            self.assertEqual(result["current_index"], live_index)
            self.assertEqual(result["data_source"], "DST EJ56 live test fixture")

    @patch("dst_macro.fetch_dst_macro_data")
    def test_early_warning_uses_supplied_live_period(self, mock_fetch):
        series = self.live_data["segments"]["copenhagen_apartments"]["series"]
        mock_fetch.return_value = {
            "unemployment_rate": 0.035,
            "rent_index": 120.0,
            "rent_series": {period: 120.0 for period in series},
            "disposable_income_cph": 400000.0,
            "disposable_income_frb": 400000.0,
            "interest_rate": 0.03,
        }

        result = check_early_warnings(
            segment="copenhagen_apartments",
            dst_data=self.live_data,
        )

        self.assertEqual(result["data_source"], "DST EJ56 live test fixture")
        self.assertEqual(result["data_observation_period"], sorted(series)[-1])


if __name__ == "__main__":
    unittest.main()
