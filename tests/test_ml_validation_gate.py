#!/usr/bin/env python3
"""The ML gate must fail closed while the real archive is still incomplete."""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.train_ews_model import _grouped_quarter_splits, train


class TestMlValidationGate(unittest.TestCase):
    def test_empty_panel_is_unavailable_and_does_not_write_model(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            panel = root / "panel.jsonl"
            report_path = root / "report.json"
            model_path = root / "model.skops"
            result = train(
                panel_path=panel,
                price_payload_path=Path(__file__).resolve().parent.parent
                / "dashboard"
                / "public"
                / "data"
                / "latest_pipeline.json",
                model_path=model_path,
                report_path=report_path,
                allow_insufficient=True,
            )
            self.assertEqual(result["status"], "INSUFFICIENT_HISTORY")
            self.assertFalse(result["deployed_model_validated"])
            self.assertFalse(model_path.exists())
            saved = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertEqual(saved["status"], "INSUFFICIENT_HISTORY")
            self.assertEqual(set(saved["coverage_by_segment"]), {
                "copenhagen_apartments",
                "copenhagen_houses",
                "frederiksberg_apartments",
            })
            self.assertTrue(any("copenhagen_apartments needs" in reason for reason in saved["reasons"]))

    def test_calibration_splits_keep_all_segments_of_a_quarter_together(self):
        rows = [
            {"observation_period": f"{year}Q{quarter}", "segment": segment}
            for year, quarter in ((2023, 1), (2023, 2), (2023, 3), (2023, 4),
                                  (2024, 1), (2024, 2), (2024, 3), (2024, 4),
                                  (2025, 1), (2025, 2), (2025, 3), (2025, 4))
            for segment in ("copenhagen_apartments", "copenhagen_houses", "frederiksberg_apartments")
        ]
        splits = _grouped_quarter_splits(rows)
        self.assertEqual(len(splits), 3)
        for train_indices, test_indices in splits:
            train_quarters = {rows[index]["observation_period"] for index in train_indices}
            test_quarters = {rows[index]["observation_period"] for index in test_indices}
            self.assertTrue(train_quarters.isdisjoint(test_quarters))
            for quarter in test_quarters:
                self.assertEqual(
                    {rows[index]["segment"] for index in test_indices if rows[index]["observation_period"] == quarter},
                    {"copenhagen_apartments", "copenhagen_houses", "frederiksberg_apartments"},
                )


if __name__ == "__main__":
    unittest.main()
