#!/usr/bin/env python3
"""Train and validate the EWS crash-probability model on real snapshots only.

The former version generated synthetic rows and used a random train/test split.
That path is deliberately gone.  This command consumes the point-in-time
feature panel written by the daily pipeline, creates 12-month labels from the
separate DST price history, evaluates expanding-window out-of-sample
predictions, and writes a model artifact only when the validation gate passes.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

import numpy as np
import skops.io as sio
from sklearn.calibration import CalibratedClassifierCV
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import log_loss as sklearn_log_loss
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import TimeSeriesSplit
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from server.ml_feature_panel import (  # noqa: E402
    FEATURE_DEFINITION_VERSION,
    FEATURE_NAMES,
    FeaturePanelError,
    SEGMENTS,
    _quarter_ordinal,
    label_rows,
    load_panel,
    summarize_labeled_rows,
    validate_panel,
)


DEFAULT_PANEL = ROOT / "data" / "ml_feature_snapshots.jsonl"
DEFAULT_PRICE_PAYLOAD = ROOT / "dashboard" / "public" / "data" / "latest_pipeline.json"
DEFAULT_MODEL = ROOT / "config" / "ews_ml_model.skops"
DEFAULT_REPORT = ROOT / "reports" / "ml_validation_latest.json"
CALIBRATION_SPLITS = 3
MIN_SEGMENT_LABELLED_ROWS = 8
MIN_SEGMENT_OOS_PREDICTIONS = 8


def _load_price_series(path: Path) -> dict[str, dict[str, float]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    segments = payload.get("dst_data", {}).get("segments", {})
    return {
        segment: {str(period): float(value) for period, value in data.get("series", {}).items()}
        for segment, data in segments.items()
    }


def _dedupe_earliest_snapshot_per_period(rows: list[dict]) -> list[dict]:
    """Use one point-in-time row per segment/quarter for model evaluation.

    Daily archives can contain several vintages for the same quarterly price
    observation. Selecting the earliest recorded vintage is conservative: a
    later revision may have been retrieved after the forward label period and
    could leak information into a supposedly out-of-sample row. The source
    vintage timestamps remain in the selected row for auditability.
    """
    selected: dict[tuple[str, str], dict] = {}
    for row in rows:
        key = (str(row["segment"]), str(row["observation_period"]))
        current = selected.get(key)
        if current is None or str(row["snapshot_at"]) < str(current["snapshot_at"]):
            selected[key] = dict(row)
    return sorted(
        selected.values(),
        key=lambda row: (_quarter_ordinal(str(row["observation_period"])), str(row["segment"])),
    )


def _fit_base_model(train_rows: list[dict]):
    x_train = np.asarray([[row["features"][name] for name in FEATURE_NAMES] for row in train_rows], dtype=float)
    y_train = np.asarray([int(row["crash_event"]) for row in train_rows], dtype=int)
    if len(np.unique(y_train)) < 2:
        return None, float(np.mean(y_train))
    model = make_pipeline(
        StandardScaler(),
        LogisticRegression(class_weight="balanced", max_iter=2000, random_state=42),
    )
    model.fit(x_train, y_train)
    return model, None


def _calibration_bins(y_true: list[int], probabilities: list[float], bins: int = 10) -> list[dict]:
    result = []
    for index in range(bins):
        lower = index / bins
        upper = (index + 1) / bins
        selected = [
            position
            for position, probability in enumerate(probabilities)
            if lower <= probability < upper or (index == bins - 1 and probability == upper)
        ]
        if not selected:
            continue
        predicted = float(np.mean([probabilities[position] for position in selected]))
        observed = float(np.mean([y_true[position] for position in selected]))
        result.append(
            {
                "lower": lower,
                "upper": upper,
                "count": len(selected),
                "mean_predicted": round(predicted, 6),
                "observed_rate": round(observed, 6),
                "absolute_error": round(abs(predicted - observed), 6),
            }
        )
    return result


def _walk_forward_predictions(rows: list[dict], min_train_observations: int) -> list[dict]:
    predictions = []
    ordered = sorted(rows, key=lambda row: (_quarter_ordinal(row["observation_period"]), row["segment"]))
    for row in ordered:
        current_ordinal = _quarter_ordinal(row["observation_period"])
        train_rows = [
            candidate
            for candidate in ordered
            if _quarter_ordinal(candidate["observation_period"]) < current_ordinal
        ]
        if len(train_rows) < min_train_observations:
            continue
        model, prior = _fit_base_model(train_rows)
        features = np.asarray([[row["features"][name] for name in FEATURE_NAMES]], dtype=float)
        probability = prior if model is None else float(model.predict_proba(features)[0, 1])
        predictions.append(
            {
                "segment": row["segment"],
                "quarter": row["observation_period"],
                "probability": round(min(max(float(probability), 0.0), 1.0), 6),
                "crash_event": int(row["crash_event"]),
                "model_status": "empirical_prior" if model is None else "walk_forward_logistic",
            }
        )
    return predictions


def _grouped_quarter_splits(rows: list[dict], n_splits: int = CALIBRATION_SPLITS):
    """Create expanding calibration folds that never split a quarter.

    The panel has one row per segment and quarter.  A row-level
    ``TimeSeriesSplit`` could place two segments from the same quarter on
    opposite sides of a fold, which leaks same-period information into
    calibration.  Splitting the unique quarters first keeps the temporal
    boundary explicit.
    """
    quarters = sorted({_quarter_ordinal(row["observation_period"]) for row in rows})
    if len(quarters) <= n_splits:
        raise FeaturePanelError(
            f"need more than {n_splits} distinct quarters for grouped calibration; found {len(quarters)}"
        )
    quarter_splits = TimeSeriesSplit(n_splits=n_splits).split(np.arange(len(quarters)))
    splits = []
    for train_quarter_indices, test_quarter_indices in quarter_splits:
        train_quarters = {quarters[index] for index in train_quarter_indices}
        test_quarters = {quarters[index] for index in test_quarter_indices}
        train_indices = [
            index
            for index, row in enumerate(rows)
            if _quarter_ordinal(row["observation_period"]) in train_quarters
        ]
        test_indices = [
            index
            for index, row in enumerate(rows)
            if _quarter_ordinal(row["observation_period"]) in test_quarters
        ]
        splits.append((train_indices, test_indices))
    return splits


def _coverage_by_segment(labeled_rows: list[dict], predictions: list[dict]) -> dict:
    coverage = {}
    for segment in SEGMENTS:
        segment_rows = [row for row in labeled_rows if row.get("segment") == segment]
        segment_predictions = [row for row in predictions if row.get("segment") == segment]
        summary = summarize_labeled_rows(segment_rows)
        coverage[segment] = {
            **summary,
            "oos_predictions": len(segment_predictions),
        }
    return coverage


def _metrics(predictions: list[dict]) -> dict:
    y_true = [int(row["crash_event"]) for row in predictions]
    probabilities = [float(row["probability"]) for row in predictions]
    if not predictions:
        return {
            "brier_score": None,
            "log_loss": None,
            "roc_auc": None,
            "calibration": [],
        }
    brier = float(np.mean((np.asarray(probabilities) - np.asarray(y_true)) ** 2))
    has_both_classes = len(set(y_true)) == 2
    return {
        "brier_score": round(brier, 6),
        "log_loss": round(float(sklearn_log_loss(y_true, probabilities, labels=[0, 1]),), 6)
        if has_both_classes
        else None,
        "roc_auc": round(float(roc_auc_score(y_true, probabilities)), 6) if has_both_classes else None,
        "calibration": _calibration_bins(y_true, probabilities),
    }


def _report(
    *,
    panel_report: dict,
    labeled_summary: dict,
    labeled_rows: list[dict],
    predictions: list[dict],
    min_train_observations: int,
    min_independent_events: int,
    min_segment_labelled_rows: int,
    min_segment_oos_predictions: int,
    error: str | None = None,
) -> dict:
    metrics = _metrics(predictions)
    coverage = _coverage_by_segment(labeled_rows, predictions)
    reasons = []
    if panel_report.get("status") != "VALID":
        reasons.append("feature panel is invalid")
    if labeled_summary.get("rows", 0) < min_train_observations:
        reasons.append(
            f"need at least {min_train_observations} labelled rows; "
            f"found {labeled_summary.get('rows', 0)}"
        )
    if labeled_summary.get("independent_event_episodes", 0) < min_independent_events:
        reasons.append(
            f"need at least {min_independent_events} independent crash episodes; "
            f"found {labeled_summary.get('independent_event_episodes', 0)}"
        )
    if len(predictions) < min_train_observations:
        reasons.append(
            f"need at least {min_train_observations} walk-forward predictions; found {len(predictions)}"
        )
    for segment, segment_coverage in coverage.items():
        if segment_coverage["rows"] < min_segment_labelled_rows:
            reasons.append(
                f"{segment} needs at least {min_segment_labelled_rows} labelled rows; "
                f"found {segment_coverage['rows']}"
            )
        if segment_coverage["oos_predictions"] < min_segment_oos_predictions:
            reasons.append(
                f"{segment} needs at least {min_segment_oos_predictions} walk-forward predictions; "
                f"found {segment_coverage['oos_predictions']}"
            )
    if error:
        reasons.append(error)
    status = "VALIDATION_AVAILABLE" if not reasons else "INSUFFICIENT_HISTORY"
    return {
        "report_schema_version": 1,
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "model_type": "walk_forward_logistic_with_time_series_calibration",
        "deployed_model_validated": status == "VALIDATION_AVAILABLE",
        "feature_definition_version": FEATURE_DEFINITION_VERSION,
        "feature_names": list(FEATURE_NAMES),
        "event_definition": "DST EJ56 index decline >= 10% over the following four quarters",
        "panel": panel_report,
        "label_summary": labeled_summary,
        "coverage_by_segment": coverage,
        "oos_predictions": len(predictions),
        "metrics": metrics,
        "calibration_method": "sigmoid_time_series_cv" if status == "VALIDATION_AVAILABLE" else None,
        "calibration_grouping": "quarter",
        "status": status,
        "reasons": reasons,
    }


def train(
    *,
    panel_path: Path = DEFAULT_PANEL,
    price_payload_path: Path = DEFAULT_PRICE_PAYLOAD,
    model_path: Path = DEFAULT_MODEL,
    report_path: Path = DEFAULT_REPORT,
    min_train_observations: int = 24,
    min_independent_events: int = 3,
    min_segment_labelled_rows: int = MIN_SEGMENT_LABELLED_ROWS,
    min_segment_oos_predictions: int = MIN_SEGMENT_OOS_PREDICTIONS,
    allow_insufficient: bool = False,
) -> dict:
    rows = load_panel(panel_path)
    panel_report = validate_panel(rows)
    labeled_rows: list[dict] = []
    error = None
    if panel_report["status"] == "VALID" and rows:
        try:
            price_series = _load_price_series(price_payload_path)
            selected = _dedupe_earliest_snapshot_per_period(rows)
            labeled_rows = label_rows(selected, price_series)
        except (FeaturePanelError, OSError, json.JSONDecodeError) as exc:
            error = str(exc)

    labeled_summary = summarize_labeled_rows(labeled_rows)
    predictions = _walk_forward_predictions(labeled_rows, min_train_observations)
    report = _report(
        panel_report=panel_report,
        labeled_summary=labeled_summary,
        labeled_rows=labeled_rows,
        predictions=predictions,
        min_train_observations=min_train_observations,
        min_independent_events=min_independent_events,
        min_segment_labelled_rows=min_segment_labelled_rows,
        min_segment_oos_predictions=min_segment_oos_predictions,
        error=error,
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    if report["status"] != "VALIDATION_AVAILABLE":
        if not allow_insufficient:
            raise FeaturePanelError("; ".join(report["reasons"]))
        return report

    x = np.asarray([[row["features"][name] for name in FEATURE_NAMES] for row in labeled_rows], dtype=float)
    y = np.asarray([int(row["crash_event"]) for row in labeled_rows], dtype=int)
    base = make_pipeline(
        StandardScaler(),
        LogisticRegression(class_weight="balanced", max_iter=2000, random_state=42),
    )
    calibrated = CalibratedClassifierCV(
        estimator=base,
        method="sigmoid",
        cv=_grouped_quarter_splits(labeled_rows),
    )
    try:
        calibrated.fit(x, y)
    except Exception as exc:  # pragma: no cover - depends on eventual data shape
        report["status"] = "CALIBRATION_FAILED"
        report["deployed_model_validated"] = False
        report["reasons"] = [f"time-series calibration failed: {exc}"]
        report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        if not allow_insufficient:
            raise FeaturePanelError(report["reasons"][0]) from exc
        return report

    model_path.parent.mkdir(parents=True, exist_ok=True)
    sio.dump(
        {
            "artifact_schema_version": 1,
            "feature_definition_version": FEATURE_DEFINITION_VERSION,
            "feature_names": list(FEATURE_NAMES),
            "model": calibrated,
            "validation_report": report,
        },
        model_path,
    )
    report["artifact"] = str(model_path)
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--panel", type=Path, default=DEFAULT_PANEL)
    parser.add_argument("--price-payload", type=Path, default=DEFAULT_PRICE_PAYLOAD)
    parser.add_argument("--model", type=Path, default=DEFAULT_MODEL)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--min-train-observations", type=int, default=24)
    parser.add_argument("--min-independent-events", type=int, default=3)
    parser.add_argument("--min-segment-labelled-rows", type=int, default=MIN_SEGMENT_LABELLED_ROWS)
    parser.add_argument("--min-segment-oos-predictions", type=int, default=MIN_SEGMENT_OOS_PREDICTIONS)
    parser.add_argument(
        "--allow-insufficient",
        action="store_true",
        help="write an explicit unavailable report and exit successfully while history is being collected",
    )
    args = parser.parse_args()
    try:
        report = train(
            panel_path=args.panel,
            price_payload_path=args.price_payload,
            model_path=args.model,
            report_path=args.report,
            min_train_observations=args.min_train_observations,
            min_independent_events=args.min_independent_events,
            min_segment_labelled_rows=args.min_segment_labelled_rows,
            min_segment_oos_predictions=args.min_segment_oos_predictions,
            allow_insufficient=args.allow_insufficient,
        )
    except FeaturePanelError as exc:
        print(f"ML validation gate blocked publication: {exc}", file=sys.stderr)
        return 2
    print(json.dumps({key: value for key, value in report.items() if key != "panel"}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
