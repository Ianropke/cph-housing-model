#!/usr/bin/env python3
"""Validate the archived point-in-time ML feature panel."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from server.ml_feature_panel import (  # noqa: E402
    FeaturePanelError,
    label_rows,
    load_panel,
    summarize_labeled_rows,
    validate_panel,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("panel", type=Path)
    parser.add_argument(
        "--price-payload",
        type=Path,
        help="optional generated payload used to derive the forward crash labels",
    )
    parser.add_argument("--min-labelled-rows", type=int, default=24)
    parser.add_argument("--min-independent-events", type=int, default=3)
    parser.add_argument(
        "--allow-insufficient",
        action="store_true",
        help="return success while the archive is still being collected",
    )
    args = parser.parse_args()

    rows = load_panel(args.panel)
    panel_report = validate_panel(rows)
    report = {"panel": panel_report}
    if panel_report["status"] != "VALID":
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return 1

    if args.price_payload:
        try:
            payload = json.loads(args.price_payload.read_text(encoding="utf-8"))
            price_series = {
                segment: data.get("series", {})
                for segment, data in payload.get("dst_data", {}).get("segments", {}).items()
            }
            labeled = label_rows(rows, price_series)
            summary = summarize_labeled_rows(labeled)
            report["labels"] = summary
            reasons = []
            if summary["rows"] < args.min_labelled_rows:
                reasons.append(
                    f"need at least {args.min_labelled_rows} labelled rows; found {summary['rows']}"
                )
            if summary["independent_event_episodes"] < args.min_independent_events:
                reasons.append(
                    f"need at least {args.min_independent_events} independent crash episodes; "
                    f"found {summary['independent_event_episodes']}"
                )
            report["status"] = "VALIDATION_AVAILABLE" if not reasons else "INSUFFICIENT_HISTORY"
            report["reasons"] = reasons
        except (OSError, json.JSONDecodeError, FeaturePanelError) as exc:
            report["status"] = "INVALID"
            report["reasons"] = [str(exc)]
    else:
        report["status"] = "VALID_PANEL_HISTORY_NOT_LABELLED"
        report["reasons"] = ["Pass --price-payload to evaluate forward crash labels"]

    print(json.dumps(report, indent=2, ensure_ascii=False))
    if report["status"] in {"VALIDATION_AVAILABLE", "VALID_PANEL_HISTORY_NOT_LABELLED"}:
        return 0
    return 0 if args.allow_insufficient and report["status"] == "INSUFFICIENT_HISTORY" else 2


if __name__ == "__main__":
    raise SystemExit(main())
