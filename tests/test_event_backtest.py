"""
Unit test suite verifying Event Prediction Crash Backtest engine.
Validates precision, recall, Brier score, and lead time metrics.
"""

import unittest
import os
import sys

# Ensure scripts directory is on PYTHONPATH
scripts_dir = os.path.join(os.path.dirname(__file__), "..", "scripts")
if scripts_dir not in sys.path:
    sys.path.insert(0, scripts_dir)

from evaluate_event_prediction import evaluate_crash_event_prediction


class TestEventBacktest(unittest.TestCase):
    def test_evaluate_crash_event_prediction_keys(self):
        """Verifies structure and keys of crash event prediction output."""
        res = evaluate_crash_event_prediction()
        self.assertIn("event_definition", res)
        self.assertIn("sample_quarters_evaluated", res)
        self.assertIn("confusion_matrix", res)
        self.assertIn("metrics", res)

    def test_confusion_matrix_bounds(self):
        """Verifies confusion matrix counts sum up to sample quarters."""
        res = evaluate_crash_event_prediction()
        cm = res["confusion_matrix"]
        total = cm["true_positives"] + cm["false_positives"] + cm["true_negatives"] + cm["false_negatives"]
        self.assertEqual(total, res["sample_quarters_evaluated"])

    def test_brier_score_validity(self):
        """Verifies Brier score is within valid probability bound [0, 1]."""
        res = evaluate_crash_event_prediction()
        brier = res["metrics"]["brier_score"]
        self.assertGreaterEqual(brier, 0.0)
        self.assertLessEqual(brier, 1.0)

    def test_warning_lead_time(self):
        """Verifies positive average lead time is reported."""
        res = evaluate_crash_event_prediction()
        lead_time = res["metrics"]["average_lead_time_months"]
        self.assertGreater(lead_time, 0.0)


if __name__ == "__main__":
    unittest.main()
