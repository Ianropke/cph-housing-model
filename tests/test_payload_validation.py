import copy
import datetime as dt
import json
import unittest
from pathlib import Path

from payload_validation import validate_pipeline_payload


ROOT = Path(__file__).resolve().parents[1]


class TestPayloadValidation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with (ROOT / "dashboard/public/data/latest_pipeline.json").open() as handle:
            cls.payload = json.load(handle)

    def test_current_payload_shape_is_valid_at_generation_time(self):
        payload = copy.deepcopy(self.payload)
        payload["schema_version"] = 1
        for segment in payload["dst_data"]["segments"]:
            dst = payload["dst_data"]["segments"][segment]
            forecast = payload["forecasts"][segment]
            forecast["current_period"] = dst["latest_period"]
            forecast["current_index"] = dst["latest_value"]
        generated = dt.datetime.fromisoformat(payload["generated_at"])
        self.assertEqual(validate_pipeline_payload(payload, now=generated), [])

    def test_period_mismatch_is_rejected(self):
        payload = copy.deepcopy(self.payload)
        payload["schema_version"] = 1
        payload["forecasts"]["copenhagen_apartments"]["current_period"] = "1900Q1"
        generated = dt.datetime.fromisoformat(payload["generated_at"])
        errors = validate_pipeline_payload(payload, now=generated)
        self.assertTrue(any("current_period" in error for error in errors))

    def test_stale_payload_is_rejected(self):
        payload = copy.deepcopy(self.payload)
        payload["schema_version"] = 1
        generated = dt.datetime.fromisoformat(payload["generated_at"])
        errors = validate_pipeline_payload(payload, now=generated + dt.timedelta(hours=49))
        self.assertTrue(any("stale" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
