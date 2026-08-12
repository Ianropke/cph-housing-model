"""Validation for the generated dashboard payload.

The validator is intentionally dependency-free so it can run as a publication
gate in CI before a generated file is committed.
"""
from __future__ import annotations

import datetime as dt
import math
from typing import Any


REQUIRED_SEGMENTS = (
    "copenhagen_apartments",
    "copenhagen_houses",
    "frederiksberg_apartments",
)
REQUIRED_HORIZONS = ("6m", "12m", "24m")
REQUIRED_MODES = ("yoy_original", "yoy_expanded", "structural_3y", "structural_5y")


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def _parse_timestamp(value: Any) -> dt.datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is not None:
        parsed = parsed.astimezone(dt.timezone.utc).replace(tzinfo=None)
    return parsed


def validate_pipeline_payload(
    payload: Any,
    *,
    now: dt.datetime | None = None,
    max_age_hours: float = 48,
) -> list[str]:
    """Return all schema, lineage, freshness and period-alignment errors."""
    errors: list[str] = []
    if not isinstance(payload, dict):
        return ["payload must be a JSON object"]

    if payload.get("schema_version") != 1:
        errors.append("schema_version must be 1")

    generated_at = _parse_timestamp(payload.get("generated_at"))
    if generated_at is None:
        errors.append("generated_at must be a valid ISO-8601 timestamp")
    else:
        reference_now = now or dt.datetime.now()
        if reference_now.tzinfo is not None:
            reference_now = reference_now.astimezone(dt.timezone.utc).replace(tzinfo=None)
        age_hours = (reference_now - generated_at).total_seconds() / 3600
        if age_hours < -1:
            errors.append("generated_at is in the future")
        elif age_hours > max_age_hours:
            errors.append(f"payload is stale ({age_hours:.1f} hours old; limit {max_age_hours:g})")

    market_status = payload.get("market_data_status")
    if not isinstance(market_status, dict):
        errors.append("market_data_status is required")
    else:
        if market_status.get("status") != "live":
            errors.append("market_data_status.status must be live")
        if _parse_timestamp(market_status.get("generated_at")) is None:
            errors.append("market_data_status.generated_at must be a valid ISO-8601 timestamp")
        if not isinstance(market_status.get("sources"), dict) or not market_status["sources"]:
            errors.append("market_data_status.sources must be a non-empty object")

    dst_data = payload.get("dst_data")
    if not isinstance(dst_data, dict) or not isinstance(dst_data.get("segments"), dict):
        errors.append("dst_data.segments is required")
        dst_segments: dict[str, Any] = {}
    else:
        dst_segments = dst_data["segments"]

    forecasts = payload.get("forecasts")
    if not isinstance(forecasts, dict):
        errors.append("forecasts is required")
        forecasts = {}

    early_warnings = payload.get("early_warnings")
    if not isinstance(early_warnings, dict):
        errors.append("early_warnings is required")
        early_warnings = {}

    for segment in REQUIRED_SEGMENTS:
        dst_segment = dst_segments.get(segment)
        if not isinstance(dst_segment, dict):
            errors.append(f"{segment}: missing DST segment")
            continue
        latest_period = dst_segment.get("latest_period")
        latest_value = dst_segment.get("latest_value")
        series = dst_segment.get("series")
        if not isinstance(latest_period, str) or not latest_period:
            errors.append(f"{segment}: latest_period is required")
        if not _is_number(latest_value):
            errors.append(f"{segment}: latest_value must be numeric")
        if not isinstance(series, dict) or not series:
            errors.append(f"{segment}: series must be non-empty")
        elif latest_period not in series:
            errors.append(f"{segment}: latest_period is absent from series")

        forecast = forecasts.get(segment)
        if not isinstance(forecast, dict):
            errors.append(f"{segment}: missing forecast")
        else:
            if forecast.get("current_period") != latest_period:
                errors.append(
                    f"{segment}: forecast current_period {forecast.get('current_period')!r} "
                    f"does not match DST {latest_period!r}"
                )
            if _is_number(latest_value) and _is_number(forecast.get("current_index")):
                if abs(float(forecast["current_index"]) - float(latest_value)) > 1e-9:
                    errors.append(f"{segment}: forecast current_index does not match DST latest_value")
            elif not _is_number(forecast.get("current_index")):
                errors.append(f"{segment}: forecast current_index must be numeric")
            horizons = forecast.get("horizons")
            if not isinstance(horizons, dict):
                errors.append(f"{segment}: forecast horizons are required")
            else:
                for horizon in REQUIRED_HORIZONS:
                    if not isinstance(horizons.get(horizon), dict) or not isinstance(
                        horizons[horizon].get("ensemble"), dict
                    ):
                        errors.append(f"{segment}: forecast horizon {horizon} is incomplete")

        ewi = early_warnings.get(segment)
        if not isinstance(ewi, dict):
            errors.append(f"{segment}: missing early-warning result")
        else:
            if not _is_number(ewi.get("composite_score")):
                errors.append(f"{segment}: composite_score must be numeric")
            modes = ewi.get("modes")
            if not isinstance(modes, dict):
                errors.append(f"{segment}: EWI modes are required")
            else:
                for mode in REQUIRED_MODES:
                    mode_data = modes.get(mode)
                    if not isinstance(mode_data, dict) or not isinstance(mode_data.get("earlyWarningIndicators"), list):
                        errors.append(f"{segment}: EWI mode {mode} is incomplete")

    return errors
