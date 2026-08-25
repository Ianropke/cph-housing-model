"""Guarded production loading for the validated EWS probability artifact."""
from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import skops.io as sio

from ml_feature_panel import FEATURE_DEFINITION_VERSION, FEATURE_NAMES


ROOT = Path(__file__).resolve().parent.parent
MODEL_PATH = ROOT / "config" / "ews_ml_model.skops"
REPORT_PATH = ROOT / "reports" / "ml_validation_latest.json"


def _validated_bundle() -> tuple[object | None, str]:
    """Load only an artifact accompanied by a passing validation report."""
    if not REPORT_PATH.exists():
        return None, "UNAVAILABLE_UNVALIDATED_MODEL"
    try:
        report = json.loads(REPORT_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None, "UNAVAILABLE_UNVALIDATED_MODEL"
    if report.get("status") != "VALIDATION_AVAILABLE" or not report.get("deployed_model_validated"):
        return None, "UNAVAILABLE_UNVALIDATED_MODEL"
    if report.get("feature_definition_version") != FEATURE_DEFINITION_VERSION:
        return None, "UNAVAILABLE_MODEL_ARTIFACT"
    if report.get("feature_names") != list(FEATURE_NAMES) or not MODEL_PATH.exists():
        return None, "UNAVAILABLE_MODEL_ARTIFACT"
    try:
        trusted = sio.get_untrusted_types(file=str(MODEL_PATH))
        bundle = sio.load(str(MODEL_PATH), trusted=trusted)
    except Exception:
        return None, "UNAVAILABLE_MODEL_ARTIFACT"
    if (
        not isinstance(bundle, dict)
        or bundle.get("feature_definition_version") != FEATURE_DEFINITION_VERSION
        or bundle.get("feature_names") != list(FEATURE_NAMES)
    ):
        return None, "UNAVAILABLE_MODEL_ARTIFACT"
    return bundle.get("model"), "VALIDATED"


def predict_probability(features: dict[str, float]) -> tuple[float | None, str]:
    """Return a guarded probability and its explicit model status."""
    missing = [name for name in FEATURE_NAMES if name not in features]
    if missing:
        return None, "UNAVAILABLE_INVALID_FEATURES"
    try:
        values = [float(features[name]) for name in FEATURE_NAMES]
    except (TypeError, ValueError):
        return None, "UNAVAILABLE_INVALID_FEATURES"
    if any(not math.isfinite(value) for value in values):
        return None, "UNAVAILABLE_INVALID_FEATURES"
    model, status = _validated_bundle()
    if model is None:
        return None, status
    try:
        probability = float(model.predict_proba(np.asarray([values], dtype=float))[0, 1])
    except Exception:
        return None, "UNAVAILABLE_MODEL_ARTIFACT"
    if not math.isfinite(probability) or not 0.0 <= probability <= 1.0:
        return None, "UNAVAILABLE_INVALID_PREDICTION"
    return round(probability, 3), status
