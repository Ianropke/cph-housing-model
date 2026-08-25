"""Event-based crash evaluation using strictly walk-forward predictions.

This module deliberately does NOT evaluate the deployed seven-feature ML model,
because the repository does not contain sufficient historical point-in-time
snapshots of its features. Instead it evaluates a transparent price-only benchmark using the
same crash-event definition. Results must never be presented as validation of
the deployed ML probability.
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import log_loss, roc_auc_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler


ROOT = Path(__file__).resolve().parent.parent
SERVER_DIR = ROOT / "server"
if str(SERVER_DIR) not in sys.path:
    sys.path.insert(0, str(SERVER_DIR))


def _fetch_dst_prices() -> tuple[list[str], list[float], str]:
    """Use the same EJ56 adapter as the production pipeline.

    The former GET query omitted the time dimension and consistently fell back
    to the short repository seed. Keeping one adapter avoids testing a
    different data path from the one used to produce the dashboard payload.
    """
    from cph_housing_server import fetch_dst_housing_data

    data = fetch_dst_housing_data(segment="copenhagen_apartments")
    series = data["segments"]["copenhagen_apartments"]["series"]
    periods = sorted(series)
    source = data.get("source", "DST EJ56 live API")
    return periods, [float(series[p]) for p in periods], source


def _features(prices: list[float], i: int) -> list[float] | None:
    if i < 8:
        return None
    p = prices[i]
    yoy = p / prices[i - 4] - 1.0
    momentum_2y = p / prices[i - 8] - 1.0
    qoq = np.diff(np.log(np.asarray(prices[i - 4 : i + 1], dtype=float)))
    volatility = float(np.std(qoq, ddof=1)) if len(qoq) > 1 else 0.0
    drawdown = p / max(prices[i - 7 : i + 1]) - 1.0
    yoy_prev = prices[i - 1] / prices[i - 5] - 1.0
    acceleration = yoy - yoy_prev
    return [yoy, momentum_2y, volatility, drawdown, acceleration]


def _event(prices: list[float], i: int, threshold: float) -> int:
    if i + 4 >= len(prices):
        raise IndexError
    forward_change = prices[i + 4] / prices[i] - 1.0
    return int(forward_change <= threshold)


def _calibration_bins(y_true: list[int], probs: list[float], bins: int = 10) -> list[dict]:
    result = []
    for b in range(bins):
        lo, hi = b / bins, (b + 1) / bins
        idx = [i for i, p in enumerate(probs) if lo <= p < hi or (b == bins - 1 and p == hi)]
        if not idx:
            continue
        predicted = float(np.mean([probs[i] for i in idx]))
        observed = float(np.mean([y_true[i] for i in idx]))
        result.append({
            "lower": lo,
            "upper": hi,
            "count": len(idx),
            "mean_predicted": round(predicted, 4),
            "observed_rate": round(observed, 4),
            "absolute_error": round(abs(predicted - observed), 4),
        })
    return result


def evaluate_crash_event_prediction(
    threshold_crash_pct: float = -0.10,
    warning_threshold_prob: float = 0.35,
    min_train_observations: int = 24,
) -> dict:
    """Run an expanding-window, one-quarter-ahead probability backtest.

The target is a nominal DST EJ56 >=10% price-index decline over the following
four quarters.
    At each prediction date, only observations strictly before that date are
    used for training. No future prices or future labels enter the features.
    """
    quarters, prices, source = _fetch_dst_prices()
    rows = []
    for i in range(8, len(prices) - 4):
        feature = _features(prices, i)
        if feature is not None:
            rows.append((i, feature, _event(prices, i, threshold_crash_pct)))

    if len(rows) <= min_train_observations:
        # A missing historical archive is a limitation of the benchmark, not a
        # reason to manufacture a statistically invalid score or fail a data
        # publication. The report remains explicit that no validation exists.
        return {
            "model_type": "walk_forward_price_only_benchmark",
            "deployed_model_validated": False,
            "data_source": source,
            "event_definition": f"Nominal DST EJ56 price-index decline >= {abs(threshold_crash_pct) * 100:.0f}% over following 12 months",
            "sample_quarters_available": len(rows),
            "sample_quarters_evaluated": 0,
            "total_crashes_observed": 0,
            "confusion_matrix": {
                "true_positives": 0,
                "false_positives": 0,
                "true_negatives": 0,
                "false_negatives": 0,
            },
            "metrics": {
                "precision": None,
                "recall_sensitivity": None,
                "specificity": None,
                "f1_score": None,
                "brier_score": None,
                "log_loss": None,
                "roc_auc": None,
                "average_lead_time_months": None,
                "events_with_pre_event_warning": 0,
            },
            "calibration": [],
            "status": "INSUFFICIENT_HISTORY",
            "reason": f"Need more than {min_train_observations} labelled quarters; only {len(rows)} are available.",
            "predictions": [],
        }

    predictions = []
    for position, (i, feature, actual) in enumerate(rows):
        train_rows = rows[:position]
        if len(train_rows) < min_train_observations:
            continue
        x_train = np.asarray([r[1] for r in train_rows], dtype=float)
        y_train = np.asarray([r[2] for r in train_rows], dtype=int)
        x_test = np.asarray([feature], dtype=float)

        if len(np.unique(y_train)) < 2:
            probability = float(np.mean(y_train))
            model_status = "empirical_prior"
        else:
            model = make_pipeline(
                StandardScaler(),
                LogisticRegression(class_weight="balanced", max_iter=1000, random_state=42),
            )
            model.fit(x_train, y_train)
            probability = float(model.predict_proba(x_test)[0, 1])
            model_status = "walk_forward_logistic"

        predictions.append({
            "quarter": quarters[i],
            "probability": round(min(max(probability, 0.0), 1.0), 6),
            "crash_event": actual,
            "model_status": model_status,
        })

    y_true = [p["crash_event"] for p in predictions]
    y_prob = [p["probability"] for p in predictions]
    y_pred = [int(p >= warning_threshold_prob) for p in y_prob]

    tp = sum(p == 1 and y == 1 for p, y in zip(y_pred, y_true))
    fp = sum(p == 1 and y == 0 for p, y in zip(y_pred, y_true))
    tn = sum(p == 0 and y == 0 for p, y in zip(y_pred, y_true))
    fn = sum(p == 0 and y == 1 for p, y in zip(y_pred, y_true))
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    specificity = tn / (tn + fp) if tn + fp else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    brier = float(np.mean((np.asarray(y_prob) - np.asarray(y_true)) ** 2))
    auc = None if len(set(y_true)) < 2 else float(roc_auc_score(y_true, y_prob))
    ll = float(log_loss(y_true, y_prob, labels=[0, 1])) if len(set(y_true)) > 1 else None

    event_indices = [i for i, y in enumerate(y_true) if y == 1]
    lead_times = []
    for event_i in event_indices:
        prior = [j for j in range(max(0, event_i - 8), event_i) if y_pred[j] == 1]
        if prior:
            lead_times.append((event_i - prior[-1]) * 3.0)

    result = {
        "model_type": "walk_forward_price_only_benchmark",
        "deployed_model_validated": False,
        "data_source": source,
        "event_definition": f"Nominal DST EJ56 price-index decline >= {abs(threshold_crash_pct) * 100:.0f}% over following 12 months",
        "sample_quarters_available": len(rows),
        "sample_quarters_evaluated": len(predictions),
        "total_crashes_observed": sum(y_true),
        "confusion_matrix": {
            "true_positives": tp,
            "false_positives": fp,
            "true_negatives": tn,
            "false_negatives": fn,
        },
        "metrics": {
            "precision": round(precision, 4),
            "recall_sensitivity": round(recall, 4),
            "specificity": round(specificity, 4),
            "f1_score": round(f1, 4),
            "brier_score": round(brier, 4),
            "log_loss": round(ll, 4) if ll is not None else None,
            "roc_auc": round(auc, 4) if auc is not None else None,
            "average_lead_time_months": round(float(np.mean(lead_times)), 2) if lead_times else None,
            "events_with_pre_event_warning": len(lead_times),
        },
        "calibration": _calibration_bins(y_true, y_prob),
        "status": "INSUFFICIENT_EVENTS" if sum(y_true) < 5 else "VALIDATION_AVAILABLE",
        "predictions": predictions,
    }
    return result


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("reports/event_backtest_latest.json"))
    args = parser.parse_args()
    report = evaluate_crash_event_prediction()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k != "predictions"}, indent=2))
