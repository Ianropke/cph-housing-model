"""Point-in-time feature panel and validation helpers for the EWS ML model.

The production dashboard currently exposes no ML probability because the old
artifact was trained on synthetic rows.  This module defines the real-data
contract needed to replace it safely:

* one immutable snapshot per pipeline run and segment;
* all eight model features with their source vintages;
* no forward-looking values in the feature row; and
* labels derived only after the observation date from a separate price series.

The panel is JSON Lines so the daily pipeline can append snapshots without
rewriting the dashboard payload.  Re-running a pipeline with the same
``snapshot_at`` is idempotent.
"""
from __future__ import annotations

import calendar
import datetime as dt
import hashlib
import json
import math
import os
import tempfile
from collections import defaultdict
from pathlib import Path
from typing import Iterable, Mapping, Sequence


PANEL_SCHEMA_VERSION = 1
FEATURE_NAMES = (
    "ewi1_price_wage_spread_pp",
    "ewi2_months_of_supply",
    "ewi3_volume_yoy_pct",
    "ewi4_price_reduction_rate_pct",
    "ewi5_dom_zscore",
    "ewi6_price_to_rent_zscore",
    "ewi7_amortization_free_share_pct",
    "ewi8_dsr_pct",
)
SEGMENTS = (
    "copenhagen_apartments",
    "copenhagen_houses",
    "frederiksberg_apartments",
)
REQUIRED_SOURCE_VINTAGES = {
    "ewi1_price_wage_spread_pp": (
        ("dst_ej56", "Danmarks Statistik"),
        ("wage_data", "Danmarks Statistik SBLON1"),
    ),
    "ewi2_months_of_supply": (("rkr_udb010", "Finans Danmark Statistikbank"),),
    "ewi3_volume_yoy_pct": (
        ("dst_ej56", "Danmarks Statistik"),
        ("rkr_udb010", "Finans Danmark Statistikbank"),
    ),
    "ewi4_price_reduction_rate_pct": (("boliga_listings", "Boliga API"),),
    "ewi5_dom_zscore": (("rkr_udb010", "Finans Danmark Statistikbank"),),
    "ewi6_price_to_rent_zscore": (
        ("dst_ej56", "Danmarks Statistik"),
        ("dst_hus1", "Danmarks Statistik"),
    ),
    "ewi7_amortization_free_share_pct": (("rkr_ul10", "Finansdanmark"),),
    "ewi8_dsr_pct": (
        ("dst_indkp107", "Danmarks Statistik"),
        ("nationalbanken_rates", "Nationalbanken"),
    ),
}
CRASH_HORIZON_QUARTERS = 4
CRASH_THRESHOLD = -0.10


class FeaturePanelError(ValueError):
    """Raised when a feature panel cannot be used for modeling."""


def _finite_number(value: object, field: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise FeaturePanelError(f"{field} must be numeric") from exc
    if not math.isfinite(number):
        raise FeaturePanelError(f"{field} must be finite")
    return number


def _iso_timestamp(value: str | dt.datetime | None) -> str:
    if value is None:
        return dt.datetime.now(dt.timezone.utc).isoformat()
    if isinstance(value, dt.datetime):
        timestamp = value
    else:
        timestamp = dt.datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=dt.timezone.utc)
    return timestamp.astimezone(dt.timezone.utc).isoformat()


def _quarter_ordinal(period: str) -> int:
    """Return a sortable integer for ``YYYYQn`` or RKR's ``YYYYKn``."""
    normalized = period.replace("K", "Q")
    try:
        year, quarter = normalized.split("Q")
        year_number = int(year)
        quarter_number = int(quarter)
    except (AttributeError, ValueError) as exc:
        raise FeaturePanelError(f"Invalid quarterly period: {period!r}") from exc
    if quarter_number not in (1, 2, 3, 4):
        raise FeaturePanelError(f"Invalid quarterly period: {period!r}")
    return year_number * 4 + quarter_number - 1


def _period_from_ordinal(ordinal: int) -> str:
    year, quarter_index = divmod(ordinal, 4)
    return f"{year}Q{quarter_index + 1}"


def _quarter_end_date(period: str) -> dt.date:
    """Return the final calendar date of a quarterly observation period."""
    ordinal = _quarter_ordinal(period)
    year, quarter_index = divmod(ordinal, 4)
    month = (quarter_index + 1) * 3
    return dt.date(year, month, calendar.monthrange(year, month)[1])


def _source_vintages(ewi_result: Mapping[str, object]) -> dict[str, list[dict]]:
    mapping = {
        "ewi1_price_wage_spread_pp": "EWI-1_price_vs_wages",
        "ewi2_months_of_supply": "EWI-2_supply_demand",
        "ewi3_volume_yoy_pct": "EWI-3_volume_price_divergence",
        "ewi4_price_reduction_rate_pct": "EWI-4_price_reductions",
        "ewi5_dom_zscore": "EWI-5_time_on_market",
        "ewi6_price_to_rent_zscore": "EWI-6_price_to_rent",
        "ewi7_amortization_free_share_pct": "EWI-7_credit_growth",
        "ewi8_dsr_pct": "EWI-8_dsr",
    }
    indicators = ewi_result.get("indicators", {})
    result = {}
    for feature, indicator_key in mapping.items():
        indicator = indicators.get(indicator_key, {})
        sources = indicator.get("data_sources", [])
        result[feature] = [
            {
                "key": source.get("key"),
                "source": source.get("source"),
                "last_updated": source.get("last_updated"),
                "frequency": source.get("frequency"),
            }
            for source in sources
        ]
    return result


def build_feature_snapshot(
    segment: str,
    ewi_result: Mapping[str, object],
    dst_segment: Mapping[str, object],
    *,
    snapshot_at: str | dt.datetime | None = None,
    source_status: str = "live",
) -> dict:
    """Convert the current live EWI result into an immutable model row."""
    if segment not in SEGMENTS:
        raise FeaturePanelError(f"Unknown segment: {segment}")
    if source_status != "live":
        raise FeaturePanelError("ML feature snapshots require live source data")

    indicators = ewi_result.get("indicators", {})

    def indicator(name: str) -> Mapping[str, object]:
        value = indicators.get(name)
        if not isinstance(value, Mapping):
            raise FeaturePanelError(f"Missing indicator: {name}")
        return value

    dom = indicator("EWI-5_time_on_market")
    dom_std = _finite_number(dom.get("baseline_std_days"), "EWI-5 baseline_std_days")
    if dom_std <= 0:
        raise FeaturePanelError("EWI-5 baseline_std_days must be positive")

    rent = indicator("EWI-6_price_to_rent")
    rent_std = _finite_number(rent.get("baseline_std"), "EWI-6 baseline_std")
    if rent_std <= 0:
        raise FeaturePanelError("EWI-6 baseline_std must be positive")

    features = {
        "ewi1_price_wage_spread_pp": _finite_number(
            indicator("EWI-1_price_vs_wages").get("spread_pp"), "ewi1_price_wage_spread_pp"
        ),
        "ewi2_months_of_supply": _finite_number(
            indicator("EWI-2_supply_demand").get("months_of_supply"), "ewi2_months_of_supply"
        ),
        "ewi3_volume_yoy_pct": _finite_number(
            indicator("EWI-3_volume_price_divergence").get("volume_yoy_pct"), "ewi3_volume_yoy_pct"
        ),
        "ewi4_price_reduction_rate_pct": _finite_number(
            indicator("EWI-4_price_reductions").get("reduction_rate_pct"),
            "ewi4_price_reduction_rate_pct",
        ),
        "ewi5_dom_zscore": round(
            (
                _finite_number(dom.get("median_dom_days"), "EWI-5 median_dom_days")
                - _finite_number(dom.get("baseline_mean_days"), "EWI-5 baseline_mean_days")
            )
            / dom_std,
            8,
        ),
        "ewi6_price_to_rent_zscore": round(
            (
                _finite_number(rent.get("price_to_rent_ratio"), "EWI-6 price_to_rent_ratio")
                - _finite_number(rent.get("baseline_mean"), "EWI-6 baseline_mean")
            )
            / rent_std,
            8,
        ),
        "ewi7_amortization_free_share_pct": _finite_number(
            indicator("EWI-7_credit_growth").get("amortization_free_share_pct"),
            "ewi7_amortization_free_share_pct",
        ),
        "ewi8_dsr_pct": _finite_number(
            indicator("EWI-8_dsr").get("dsr_pct"), "ewi8_dsr_pct"
        ),
    }

    observation_period = str(dst_segment.get("latest_period", ""))
    _quarter_ordinal(observation_period)
    price_index = _finite_number(dst_segment.get("latest_value"), "price_index")
    snapshot_timestamp = _iso_timestamp(snapshot_at or ewi_result.get("evaluation_timestamp"))
    snapshot_id = hashlib.sha256(
        f"{segment}|{observation_period}|{snapshot_timestamp}".encode("utf-8")
    ).hexdigest()[:20]

    return {
        "panel_schema_version": PANEL_SCHEMA_VERSION,
        "snapshot_id": snapshot_id,
        "segment": segment,
        "observation_period": observation_period,
        "snapshot_at": snapshot_timestamp,
        "source_status": source_status,
        "price_index": price_index,
        "price_source": "Danmarks Statistik EJ56",
        "feature_definition_version": "ews_live_v1",
        "features": features,
        "source_vintages": _source_vintages(ewi_result),
    }


def load_panel(path: str | os.PathLike[str]) -> list[dict]:
    """Load JSONL or a JSON object containing ``snapshots``."""
    panel_path = Path(path)
    if not panel_path.exists():
        return []
    text = panel_path.read_text(encoding="utf-8").strip()
    if not text:
        return []
    if text.startswith("[") or text.startswith("{"):
        try:
            payload = json.loads(text)
        except json.JSONDecodeError:
            payload = None
        if payload is not None:
            if isinstance(payload, list):
                return payload
            if isinstance(payload, dict) and "snapshots" in payload:
                rows = payload["snapshots"]
                if not isinstance(rows, list):
                    raise FeaturePanelError("JSON feature panel snapshots must be a list")
                return rows
            if isinstance(payload, dict):
                return [payload]
    return [json.loads(line) for line in text.splitlines() if line.strip()]


def append_panel(path: str | os.PathLike[str], snapshots: Iterable[Mapping[str, object]]) -> int:
    """Append snapshots atomically and idempotently; return rows added."""
    panel_path = Path(path)
    panel_path.parent.mkdir(parents=True, exist_ok=True)
    existing = load_panel(panel_path)
    by_id = {str(row.get("snapshot_id")): dict(row) for row in existing}
    before = len(by_id)
    for snapshot in snapshots:
        snapshot_id = str(snapshot.get("snapshot_id", ""))
        if not snapshot_id:
            raise FeaturePanelError("Cannot append snapshot without snapshot_id")
        by_id[snapshot_id] = dict(snapshot)
    ordered = sorted(by_id.values(), key=lambda row: (row.get("segment", ""), row.get("snapshot_at", "")))
    fd, temp_name = tempfile.mkstemp(prefix=f".{panel_path.name}.", dir=panel_path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            for row in ordered:
                handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
        os.replace(temp_name, panel_path)
    except Exception:
        try:
            os.unlink(temp_name)
        except FileNotFoundError:
            pass
        raise
    return len(by_id) - before


def validate_panel(rows: Sequence[Mapping[str, object]], *, require_live: bool = True) -> dict:
    """Return an inspectable quality report for a point-in-time panel."""
    errors: list[str] = []
    seen_ids: set[str] = set()
    seen_keys: set[tuple[str, str, str]] = set()
    counts = defaultdict(int)
    periods = defaultdict(set)

    for position, row in enumerate(rows):
        prefix = f"row {position}"
        if row.get("panel_schema_version") != PANEL_SCHEMA_VERSION:
            errors.append(f"{prefix}: unsupported panel_schema_version")
        segment = row.get("segment")
        period = row.get("observation_period")
        snapshot_at = row.get("snapshot_at")
        if segment not in SEGMENTS:
            errors.append(f"{prefix}: unknown segment")
        if not isinstance(period, str):
            errors.append(f"{prefix}: missing observation_period")
        else:
            try:
                _quarter_ordinal(period)
            except FeaturePanelError as exc:
                errors.append(f"{prefix}: {exc}")
        snapshot_time = None
        if not isinstance(snapshot_at, str):
            errors.append(f"{prefix}: missing snapshot_at")
        else:
            try:
                snapshot_time = dt.datetime.fromisoformat(snapshot_at.replace("Z", "+00:00"))
                if snapshot_time.tzinfo is None:
                    errors.append(f"{prefix}: snapshot_at must include a timezone")
            except ValueError:
                errors.append(f"{prefix}: invalid snapshot_at")
        snapshot_id = str(row.get("snapshot_id", ""))
        if not snapshot_id:
            errors.append(f"{prefix}: missing snapshot_id")
        elif snapshot_id in seen_ids:
            errors.append(f"{prefix}: duplicate snapshot_id {snapshot_id}")
        seen_ids.add(snapshot_id)
        key = (str(segment), str(period), str(snapshot_at))
        if key in seen_keys:
            errors.append(f"{prefix}: duplicate segment/period/snapshot_at")
        seen_keys.add(key)
        if require_live and row.get("source_status") != "live":
            errors.append(f"{prefix}: source_status is not live")
        try:
            _finite_number(row.get("price_index"), f"{prefix} price_index")
        except FeaturePanelError as exc:
            errors.append(str(exc))
        if row.get("feature_definition_version") != "ews_live_v1":
            errors.append(f"{prefix}: unsupported feature_definition_version")

        prohibited_fields = {
            "crash_event",
            "forward_observation_period",
            "forward_price_index",
            "forward_change_pct",
        }
        leaked = sorted(prohibited_fields.intersection(row))
        if leaked:
            errors.append(f"{prefix}: label leakage fields present: {', '.join(leaked)}")

        features = row.get("features")
        if not isinstance(features, Mapping):
            errors.append(f"{prefix}: features must be an object")
            features = {}
        missing = [name for name in FEATURE_NAMES if name not in features]
        if missing:
            errors.append(f"{prefix}: missing features: {', '.join(missing)}")
        for name in FEATURE_NAMES:
            if name in features:
                try:
                    _finite_number(features[name], f"{prefix} {name}")
                except FeaturePanelError as exc:
                    errors.append(str(exc))

        vintages = row.get("source_vintages")
        if not isinstance(vintages, Mapping):
            errors.append(f"{prefix}: source_vintages must be an object")
        else:
            for name in FEATURE_NAMES:
                if not vintages.get(name):
                    errors.append(f"{prefix}: missing source vintage for {name}")
                actual_sources = {
                    (source.get("key"), source.get("source"))
                    for source in vintages.get(name, [])
                    if isinstance(source, Mapping)
                }
                for expected_source in REQUIRED_SOURCE_VINTAGES[name]:
                    if expected_source not in actual_sources:
                        errors.append(
                            f"{prefix}: {name} missing required source identity "
                            f"{expected_source[0]} / {expected_source[1]}"
                        )
                for source in vintages.get(name, []):
                    last_updated = source.get("last_updated") if isinstance(source, Mapping) else None
                    if last_updated and snapshot_time is not None:
                        try:
                            source_date = dt.date.fromisoformat(str(last_updated)[:10])
                            if source_date > snapshot_time.date():
                                errors.append(
                                    f"{prefix}: source vintage {last_updated} is after snapshot_at {snapshot_at}"
                                )
                        except ValueError:
                            errors.append(f"{prefix}: invalid source vintage date {last_updated!r}")

        if segment in SEGMENTS:
            counts[segment] += 1
            periods[segment].add(period)

    return {
        "panel_schema_version": PANEL_SCHEMA_VERSION,
        "status": "VALID" if not errors else "INVALID",
        "rows": len(rows),
        "unique_snapshots": len(seen_ids),
        "segments": {
            segment: {
                "rows": counts[segment],
                "distinct_observation_periods": len(periods[segment]),
            }
            for segment in SEGMENTS
        },
        "errors": errors,
    }


def _independent_event_count(periods: Sequence[str], cluster_gap_quarters: int = 4) -> int:
    if not periods:
        return 0
    ordinals = sorted({_quarter_ordinal(period) for period in periods})
    episodes = 1
    for previous, current in zip(ordinals, ordinals[1:]):
        if current - previous > cluster_gap_quarters:
            episodes += 1
    return episodes


def label_rows(
    rows: Sequence[Mapping[str, object]],
    price_series_by_segment: Mapping[str, Mapping[str, object]],
    *,
    threshold: float = CRASH_THRESHOLD,
    horizon_quarters: int = CRASH_HORIZON_QUARTERS,
) -> list[dict]:
    """Attach future crash labels without exposing them as model features."""
    labeled = []
    for row in rows:
        segment = str(row.get("segment"))
        period = str(row.get("observation_period"))
        series = price_series_by_segment.get(segment, {})
        current = series.get(period)
        target_period = _period_from_ordinal(_quarter_ordinal(period) + horizon_quarters)
        future = series.get(target_period)
        if current is None or future is None:
            continue
        try:
            snapshot_at = dt.datetime.fromisoformat(str(row["snapshot_at"]).replace("Z", "+00:00"))
        except (KeyError, TypeError, ValueError):
            continue
        if snapshot_at.tzinfo is None or snapshot_at.date() > _quarter_end_date(target_period):
            # A feature row retrieved after the label horizon cannot be an
            # out-of-sample prediction, even if it describes an older quarter.
            continue
        current_price = _finite_number(current, f"{segment} {period} price")
        future_price = _finite_number(future, f"{segment} {target_period} price")
        forward_change = future_price / current_price - 1.0
        item = dict(row)
        item["crash_event"] = int(forward_change <= threshold)
        item["forward_observation_period"] = target_period
        item["forward_price_index"] = future_price
        item["forward_change_pct"] = round(forward_change * 100, 6)
        labeled.append(item)
    return labeled


def summarize_labeled_rows(rows: Sequence[Mapping[str, object]]) -> dict:
    event_periods = [str(row["observation_period"]) for row in rows if int(row["crash_event"]) == 1]
    return {
        "rows": len(rows),
        "events": sum(int(row["crash_event"]) for row in rows),
        "event_rate": (
            round(sum(int(row["crash_event"]) for row in rows) / len(rows), 6) if rows else None
        ),
        "independent_event_episodes": _independent_event_count(event_periods),
        "event_periods": sorted(set(event_periods)),
    }
