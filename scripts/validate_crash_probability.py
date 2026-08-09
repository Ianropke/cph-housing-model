"""Validate the statistical semantics of the model crash probability.

This script intentionally evaluates probabilities only when historical
out-of-sample predictions and realised crash events are available. It never
reconstructs predictions from the fitted model on its training observations.

Crash event definition: real housing-price decline of at least 10% over the
following 12 months.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Iterable


def brier_score(y_true: Iterable[int], p: Iterable[float]) -> float:
    pairs = list(zip(y_true, p))
    if not pairs:
        raise ValueError("No observations available")
    return sum((prob - actual) ** 2 for actual, prob in pairs) / len(pairs)


def log_loss(y_true: Iterable[int], p: Iterable[float], eps: float = 1e-15) -> float:
    pairs = list(zip(y_true, p))
    if not pairs:
        raise ValueError("No observations available")
    total = 0.0
    for actual, prob in pairs:
        prob = min(max(float(prob), eps), 1.0 - eps)
        total += -(actual * math.log(prob) + (1 - actual) * math.log(1 - prob))
    return total / len(pairs)


def calibration_bins(y_true: list[int], probabilities: list[float], bins: int = 10) -> list[dict]:
    result = []
    for i in range(bins):
        lo = i / bins
        hi = (i + 1) / bins
        selected = [j for j, p in enumerate(probabilities) if lo <= p < hi or (i == bins - 1 and p == hi)]
        if not selected:
            continue
        observed = sum(y_true[j] for j in selected) / len(selected)
        predicted = sum(probabilities[j] for j in selected) / len(selected)
        result.append({
            "lower": lo,
            "upper": hi,
            "count": len(selected),
            "mean_predicted": predicted,
            "observed_rate": observed,
            "absolute_calibration_error": abs(predicted - observed),
        })
    return result


def validate(rows: list[dict]) -> dict:
    if not rows:
        raise ValueError("Prediction history is empty")
    y_true = [int(r["crash_event"]) for r in rows]
    probabilities = [float(r["probability"]) for r in rows]
    if any(v not in (0, 1) for v in y_true):
        raise ValueError("crash_event must be 0 or 1")
    if any(not math.isfinite(p) or p < 0 or p > 1 for p in probabilities):
        raise ValueError("All probabilities must be finite and in [0, 1]")
    bins = calibration_bins(y_true, probabilities)
    return {
        "n": len(rows),
        "events": sum(y_true),
        "event_rate": sum(y_true) / len(y_true),
        "brier_score": brier_score(y_true, probabilities),
        "log_loss": log_loss(y_true, probabilities),
        "calibration": bins,
        "mean_absolute_calibration_error": (
            sum(b["absolute_calibration_error"] * b["count"] for b in bins) / len(rows)
            if bins else None
        ),
        "status": "INSUFFICIENT_EVENTS" if sum(y_true) < 5 else "VALIDATION_AVAILABLE",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path, help="JSON file containing out-of-sample predictions")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    payload = json.loads(args.input.read_text(encoding="utf-8"))
    rows = payload["predictions"] if isinstance(payload, dict) else payload
    report = validate(rows)
    rendered = json.dumps(report, indent=2)
    if args.output:
        args.output.write_text(rendered + "\n", encoding="utf-8")
    else:
        print(rendered)


if __name__ == "__main__":
    main()
