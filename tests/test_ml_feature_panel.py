#!/usr/bin/env python3
"""Regression tests for point-in-time ML feature archiving and labels."""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from server.ml_feature_panel import (
    FEATURE_NAMES,
    append_panel,
    build_feature_snapshot,
    label_rows,
    load_panel,
    summarize_labeled_rows,
    validate_panel,
)


ROOT = Path(__file__).resolve().parent.parent
PAYLOAD_PATH = ROOT / "dashboard" / "public" / "data" / "latest_pipeline.json"


class TestMlFeaturePanel(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.payload = json.loads(PAYLOAD_PATH.read_text(encoding="utf-8"))

    def test_live_payload_can_be_archived_with_all_seven_ml_features(self):
        snapshots = []
        for segment, ewi in self.payload["early_warnings"].items():
            snapshots.append(
                build_feature_snapshot(
                    segment,
                    ewi,
                    self.payload["dst_data"]["segments"][segment],
                    snapshot_at=self.payload["generated_at"],
                )
            )

        report = validate_panel(snapshots)
        self.assertEqual(report["status"], "VALID")
        self.assertEqual(report["rows"], 3)
        self.assertEqual(set(snapshots[0]["features"]), set(FEATURE_NAMES))
        self.assertNotIn("ewi4_price_reduction_rate_pct", snapshots[0]["features"])
        self.assertTrue(all(snapshots[0]["source_vintages"][name] for name in FEATURE_NAMES))
        self.assertEqual(
            self.payload["early_warnings"]["copenhagen_apartments"]["indicators"]["EWI-2_supply_demand"]["data_sources"][0]["source"],
            "Finans Danmark Statistikbank",
        )
        self.assertEqual(
            self.payload["early_warnings"]["copenhagen_apartments"]["indicators"]["EWI-4_price_reductions"]["data_sources"][0]["source"],
            "Boliga API",
        )

    def test_append_is_idempotent(self):
        snapshot = build_feature_snapshot(
            "copenhagen_apartments",
            self.payload["early_warnings"]["copenhagen_apartments"],
            self.payload["dst_data"]["segments"]["copenhagen_apartments"],
            snapshot_at="2026-08-20T15:34:35+00:00",
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "panel.jsonl"
            self.assertEqual(append_panel(path, [snapshot]), 1)
            self.assertEqual(append_panel(path, [snapshot]), 0)
            self.assertEqual(len(load_panel(path)), 1)

    def test_validation_rejects_wrong_source_identity(self):
        snapshot = build_feature_snapshot(
            "copenhagen_apartments",
            self.payload["early_warnings"]["copenhagen_apartments"],
            self.payload["dst_data"]["segments"]["copenhagen_apartments"],
            snapshot_at="2026-08-20T15:34:35+00:00",
        )
        snapshot["source_vintages"]["ewi2_months_of_supply"][0]["source"] = "Boliga API"
        report = validate_panel([snapshot])
        self.assertEqual(report["status"], "INVALID")
        self.assertTrue(any("required source identity" in error for error in report["errors"]))

    def test_validation_rejects_legacy_EWI4_feature_mixing(self):
        snapshot = build_feature_snapshot(
            "copenhagen_apartments",
            self.payload["early_warnings"]["copenhagen_apartments"],
            self.payload["dst_data"]["segments"]["copenhagen_apartments"],
            snapshot_at="2026-08-20T15:34:35+00:00",
        )
        snapshot["features"]["ewi4_price_reduction_rate_pct"] = 31.2
        report = validate_panel([snapshot])
        self.assertEqual(report["status"], "INVALID")
        self.assertTrue(any("unsupported features" in error for error in report["errors"]))

    def test_labeling_uses_four_future_quarters(self):
        snapshot = build_feature_snapshot(
            "copenhagen_apartments",
            self.payload["early_warnings"]["copenhagen_apartments"],
            self.payload["dst_data"]["segments"]["copenhagen_apartments"],
            snapshot_at="2020-08-20T15:34:35+00:00",
        )
        snapshot["observation_period"] = "2020Q1"
        prices = {
            "copenhagen_apartments": {
                "2020Q1": 100.0,
                "2020Q2": 101.0,
                "2020Q3": 99.0,
                "2020Q4": 98.0,
                "2021Q1": 88.0,
            }
        }
        labeled = label_rows([snapshot], prices)
        self.assertEqual(len(labeled), 1)
        self.assertEqual(labeled[0]["forward_observation_period"], "2021Q1")
        self.assertEqual(labeled[0]["crash_event"], 1)
        self.assertAlmostEqual(labeled[0]["forward_change_pct"], -12.0, places=4)

    def test_labeling_rejects_snapshot_after_forward_horizon(self):
        snapshot = build_feature_snapshot(
            "copenhagen_apartments",
            self.payload["early_warnings"]["copenhagen_apartments"],
            self.payload["dst_data"]["segments"]["copenhagen_apartments"],
            snapshot_at="2026-08-20T15:34:35+00:00",
        )
        snapshot["observation_period"] = "2020Q1"
        prices = {
            "copenhagen_apartments": {
                "2020Q1": 100.0,
                "2021Q1": 88.0,
            }
        }
        self.assertEqual(label_rows([snapshot], prices), [])

    def test_summary_does_not_count_overlapping_crisis_rows_as_independent_events(self):
        rows = [{"observation_period": period, "crash_event": 1} for period in ("2007Q4", "2008Q1", "2008Q2", "2008Q3")]
        summary = summarize_labeled_rows(rows)
        self.assertEqual(summary["events"], 4)
        self.assertEqual(summary["independent_event_episodes"], 1)


if __name__ == "__main__":
    unittest.main()
