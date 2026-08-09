"""Tests for the event-based walk-forward crash benchmark."""
import os
import sys
import unittest

scripts_dir = os.path.join(os.path.dirname(__file__), "..", "scripts")
if scripts_dir not in sys.path:
    sys.path.insert(0, scripts_dir)

from evaluate_event_prediction import evaluate_crash_event_prediction


class TestEventBacktest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = evaluate_crash_event_prediction()

    def test_evaluate_crash_event_prediction_keys(self):
        self.assertIn("event_definition", self.result)
        self.assertIn("sample_quarters_evaluated", self.result)
        self.assertIn("confusion_matrix", self.result)
        self.assertIn("metrics", self.result)
        self.assertFalse(self.result["deployed_model_validated"])

    def test_confusion_matrix_bounds(self):
        cm = self.result["confusion_matrix"]
        total = sum(cm.values())
        self.assertEqual(total, self.result["sample_quarters_evaluated"])

    def test_brier_score_validity(self):
        brier = self.result["metrics"]["brier_score"]
        self.assertGreaterEqual(brier, 0.0)
        self.assertLessEqual(brier, 1.0)

    def test_probability_bounds(self):
        for row in self.result["predictions"]:
            self.assertGreaterEqual(row["probability"], 0.0)
            self.assertLessEqual(row["probability"], 1.0)

    def test_lead_time_is_empirical(self):
        lead_time = self.result["metrics"]["average_lead_time_months"]
        self.assertTrue(lead_time is None or lead_time >= 0.0)


if __name__ == "__main__":
    unittest.main()
