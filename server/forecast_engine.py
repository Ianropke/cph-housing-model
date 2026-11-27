"""Data-driven econometric housing price forecast engine.

Combines:
1. A regularized Ridge time-series model (RidgeCV) trained strictly on live
   quarterly DST EJ56 housing prices and DST DNRENTM interest rates (2007Q1–present),
   validated via expanding-window walk-forward out-of-sample backtesting with zero
   look-ahead leakage.
2. Empirical P10–P90 uncertainty bands derived directly from the realized
   walk-forward out-of-sample residual distribution (centered at the point forecast).
3. An explicit, transparent high-frequency nowcast adjustment layer capturing
   post-quarter market signals (Finans Danmark UDB020 asking-price movement since
   the latest DST quarter, RKR time-on-market UDB030, RKR sales volume BM020, and
   Boliga active price-reduction share).

Both the pure econometric Ridge forecast and the live-adjusted forecast are
published side-by-side together with full additive driver decomposition so users
can inspect every percentage point of the prediction.
"""
from __future__ import annotations

import datetime as dt
import math
from typing import Any, Mapping

import numpy as np
from sklearn.linear_model import RidgeCV
from sklearn.preprocessing import StandardScaler


ALPHAS = (5.0, 15.0, 35.0, 75.0, 150.0)
HORIZON_QUARTERS = {"6m": 2, "12m": 4, "24m": 8}
FEATURE_SPECS = (
    ("mom1", "Kortsigtet prismomentum (1 kvt.)"),
    ("mom4", "Årsmomentum (4 kvt. EJ56)"),
    ("rate", "Renteniveau (Nationalbanken)"),
    ("dr4", "Renteændring seneste år (Δr)"),
)
MIN_WALK_FORWARD_TRAIN = 16


def _add_quarters(period: str, delta: int) -> str:
    year_str, q_str = period.split("Q", 1)
    total = int(year_str) * 4 + (int(q_str) - 1) + delta
    return f"{total // 4}Q{(total % 4) + 1}"


def _direction_label(change_pct: float, neutral_band_pct: float = 1.5) -> str:
    if change_pct >= neutral_band_pct:
        return "OP"
    if change_pct <= -neutral_band_pct:
        return "NED"
    return "FLADT"


def _compute_live_nowcast_adjustment(
    segment_nowcast: Mapping[str, Any] | None,
    segment_market: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Compute a transparent, bounded high-frequency market adjustment (in pp).

    Captures observable market friction and asking-price movement that occurred
    *after* the latest quarterly DST EJ56 release:
      - Official UDB020 asking-price change since the latest DST quarter (weight 0.65)
      - Excess time-on-market above 60-day baseline (-0.04 pp per extra day, capped at -2.5 pp)
      - Excess Boliga price-reduction share above 30% (-0.06 pp per pp above 30%, capped at -1.5 pp)
      - Negative sales-volume YoY divergence below -10% (-0.05 pp per pp below -10%, capped at -1.5 pp)
    """
    components: list[dict[str, Any]] = []
    udb_change = None
    if isinstance(segment_nowcast, Mapping):
        udb = segment_nowcast.get("rkr_udb020")
        if isinstance(udb, Mapping) and isinstance(udb.get("since_dst_quarter_change_pct"), (int, float)):
            udb_change = float(udb["since_dst_quarter_change_pct"])

    # 1. Official asking-price movement since latest DST quarter
    udb_pp = 0.0
    if udb_change is not None and math.isfinite(udb_change):
        udb_pp = max(-6.0, min(6.0, udb_change * 0.65))
        components.append({
            "key": "nowcast_udb020",
            "label": "Udbudspris efter seneste DST-kvartal (UDB020)",
            "value_display": f"{udb_change:+.1f}%",
            "impact_pp": round(udb_pp, 2),
            "source": "Finans Danmark UDB020",
        })

    # 2. Time on market (excess days above 60-day balanced baseline)
    dom_pp = 0.0
    if isinstance(segment_market, Mapping) and isinstance(segment_market.get("median_dom"), (int, float)):
        dom = float(segment_market["median_dom"])
        excess_days = dom - 60.0
        if excess_days > 0:
            dom_pp = -min(2.5, excess_days * 0.04)
        elif excess_days < -10:
            dom_pp = min(1.0, abs(excess_days + 10.0) * 0.03)
        components.append({
            "key": "nowcast_dom",
            "label": "Liggetid i markedet (UDB030)",
            "value_display": f"{int(round(dom))} dage",
            "impact_pp": round(dom_pp, 2),
            "source": "Finans Danmark UDB030",
        })

    # 3. Price reduction share (Boliga active listings)
    red_pp = 0.0
    if isinstance(segment_market, Mapping) and isinstance(segment_market.get("price_reduction_rate"), (int, float)):
        red_pct = float(segment_market["price_reduction_rate"]) * 100.0
        if red_pct > 30.0:
            red_pp = -min(1.5, (red_pct - 30.0) * 0.06)
        elif red_pct < 20.0:
            red_pp = min(0.8, (20.0 - red_pct) * 0.04)
        components.append({
            "key": "nowcast_reductions",
            "label": "Andel boliger med prisafslag (Boliga)",
            "value_display": f"{red_pct:.1f}%",
            "impact_pp": round(red_pp, 2),
            "source": "Boliga API",
        })

    # 4. Volume-price divergence (RKR BM020 sales volume YoY)
    vol_pp = 0.0
    if isinstance(segment_market, Mapping) and isinstance(segment_market.get("volume_yoy_change"), (int, float)):
        vol_pct = float(segment_market["volume_yoy_change"]) * 100.0
        if vol_pct < -10.0:
            vol_pp = -min(1.5, abs(vol_pct + 10.0) * 0.05)
        elif vol_pct > 15.0:
            vol_pp = min(1.0, (vol_pct - 15.0) * 0.03)
        components.append({
            "key": "nowcast_volume",
            "label": "Handelsvolumen år/år (BM020)",
            "value_display": f"{vol_pct:+.1f}%",
            "impact_pp": round(vol_pp, 2),
            "source": "Finans Danmark BM020",
        })

    total_6m_pp = round(udb_pp + dom_pp + red_pp + vol_pp, 2)
    # 12m carries full friction impact; 24m mean-reverts slightly toward econometric fundamentals
    horizon_multipliers = {"6m": 1.0, "12m": 1.15, "24m": 0.90}
    return {
        "base_adjustment_pp": total_6m_pp,
        "by_horizon_pp": {h: round(total_6m_pp * mult, 2) for h, mult in horizon_multipliers.items()},
        "components": components,
        "udb020_change_since_dst_pct": udb_change,
    }


def run_data_driven_forecast(
    segment: str,
    price_series: Mapping[str, float],
    rate_series: Mapping[str, float],
    *,
    segment_nowcast: Mapping[str, Any] | None = None,
    segment_market: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Run the walk-forward validated Ridge forecast engine + live nowcast bridge."""
    quarters = sorted(q for q in price_series if q in rate_series and price_series[q] > 0)
    if len(quarters) < MIN_WALK_FORWARD_TRAIN + 12:
        raise ValueError(
            f"{segment}: insufficient overlapping DST EJ56/DNRENTM history "
            f"(found {len(quarters)} quarters; need at least {MIN_WALK_FORWARD_TRAIN + 12})"
        )

    feature_rows = []
    feature_quarters = []
    for i in range(4, len(quarters)):
        q = quarters[i]
        p_now = float(price_series[q])
        p_1 = float(price_series[quarters[i - 1]])
        p_4 = float(price_series[quarters[i - 4]])
        r_now = float(rate_series[q])
        r_4 = float(rate_series[quarters[i - 4]])
        feature_rows.append([
            math.log(p_now / p_1),
            math.log(p_now / p_4),
            r_now,
            r_now - r_4,
        ])
        feature_quarters.append(q)

    x_all = np.asarray(feature_rows, dtype=float)
    latest_period = feature_quarters[-1]
    latest_index = float(price_series[latest_period])
    latest_raw_features = feature_rows[-1]

    live_bridge = _compute_live_nowcast_adjustment(segment_nowcast, segment_market)
    horizons_output: dict[str, Any] = {}

    for horizon_key, h_q in HORIZON_QUARTERS.items():
        n_labeled = len(feature_quarters) - h_q
        y_all = np.asarray(
            [math.log(float(price_series[feature_quarters[i + h_q]]) / float(price_series[feature_quarters[i]])) for i in range(n_labeled)],
            dtype=float,
        )

        # Strict expanding-window walk-forward validation (no look-ahead:
        # every training row s satisfies s + h_q <= t).
        oos_preds = []
        oos_actuals = []
        oos_naive = []
        for t in range(MIN_WALK_FORWARD_TRAIN + h_q, n_labeled):
            train_end = t - h_q + 1
            scaler_wf = StandardScaler()
            x_tr_s = scaler_wf.fit_transform(x_all[:train_end])
            model_wf = RidgeCV(alphas=ALPHAS)
            model_wf.fit(x_tr_s, y_all[:train_end])
            oos_preds.append(float(model_wf.predict(scaler_wf.transform(x_all[t : t + 1]))[0]))
            oos_actuals.append(float(y_all[t]))
            oos_naive.append(float(np.mean(y_all[:train_end])))

        oos_preds_arr = np.asarray(oos_preds, dtype=float)
        oos_actuals_arr = np.asarray(oos_actuals, dtype=float)
        oos_naive_arr = np.asarray(oos_naive, dtype=float)
        resids = oos_actuals_arr - oos_preds_arr
        centered_resids = resids - float(np.median(resids))

        mae_pct = float(np.mean(np.abs(np.exp(oos_actuals_arr) - np.exp(oos_preds_arr))) * 100.0)
        rmse_pct = float(np.sqrt(np.mean((np.exp(oos_actuals_arr) - np.exp(oos_preds_arr)) ** 2)) * 100.0)
        naive_mae_pct = float(np.mean(np.abs(np.exp(oos_actuals_arr) - np.exp(oos_naive_arr))) * 100.0)
        hit_rate_pct = float(np.mean((oos_preds_arr >= 0) == (oos_actuals_arr >= 0)) * 100.0)

        # Final fit on all available labeled quarters [0..n_labeled-1]
        scaler = StandardScaler()
        x_fit_s = scaler.fit_transform(x_all[:n_labeled])
        model = RidgeCV(alphas=ALPHAS)
        model.fit(x_fit_s, y_all)

        x_now_s = scaler.transform(x_all[-1:])
        pred_log = float(model.predict(x_now_s)[0])
        ridge_change_pct = (math.exp(pred_log) - 1.0) * 100.0
        ridge_index = latest_index * math.exp(pred_log)

        # Combine pure Ridge forecast with explicit post-quarter live market bridge
        live_adj_pp = live_bridge["by_horizon_pp"][horizon_key]
        combined_change_pct = ridge_change_pct + live_adj_pp
        combined_log = math.log(max(0.25, 1.0 + combined_change_pct / 100.0))
        combined_index = latest_index * math.exp(combined_log)

        p10_offset = float(np.percentile(centered_resids, 10))
        p90_offset = float(np.percentile(centered_resids, 90))

        p10_log = combined_log + p10_offset
        p90_log = combined_log + p90_offset
        p10_change_pct = (math.exp(p10_log) - 1.0) * 100.0
        p90_change_pct = (math.exp(p90_log) - 1.0) * 100.0
        p10_index = latest_index * math.exp(p10_log)
        p90_index = latest_index * math.exp(p90_log)

        # Driver decomposition (Ridge contributions in log-pp scaled to exact pct contribution)
        raw_contribs = model.coef_ * x_now_s[0]
        raw_displays = [
            f"{(math.exp(latest_raw_features[0]) - 1) * 100:+.1f}%",
            f"{(math.exp(latest_raw_features[1]) - 1) * 100:+.1f}%",
            f"{latest_raw_features[2] * 100:.2f}%",
            f"{latest_raw_features[3] * 100:+.2f} pp",
        ]
        econometric_drivers = [
            {
                "key": "intercept",
                "label": "Historisk grundtrend (2007–2026)",
                "value_display": f"{len(feature_quarters)} kvt.",
                "impact_pp": round(float(model.intercept_) * 100.0, 2),
                "source": "DST EJ56",
            }
        ]
        for idx, (fkey, flabel) in enumerate(FEATURE_SPECS):
            econometric_drivers.append({
                "key": fkey,
                "label": flabel,
                "value_display": raw_displays[idx],
                "impact_pp": round(float(raw_contribs[idx]) * 100.0, 2),
                "source": "DST EJ56" if fkey.startswith("mom") else "DST DNRENTM",
            })

        # Sensitivity per +1pp mortgage/policy rate shock (from fitted standardized coef)
        rate_std = float(scaler.scale_[2]) if scaler.scale_[2] > 0 else 0.01
        dr_std = float(scaler.scale_[3]) if scaler.scale_[3] > 0 else 0.01
        rate_sensitivity_per_1pp = round(
            ((float(model.coef_[2]) / rate_std) + (float(model.coef_[3]) / dr_std)) * 0.01 * 100.0,
            2,
        )

        horizons_output[horizon_key] = {
            "target_period": _add_quarters(latest_period, h_q),
            "quarters_ahead": h_q,
            "combined": {
                "forecast_index": round(combined_index, 1),
                "change_pct": round(combined_change_pct, 2),
                "p10_index": round(p10_index, 1),
                "p50_index": round(combined_index, 1),
                "p90_index": round(p90_index, 1),
                "p10_change_pct": round(p10_change_pct, 2),
                "p90_change_pct": round(p90_change_pct, 2),
                "direction": _direction_label(combined_change_pct),
            },
            "econometric_ridge": {
                "forecast_index": round(ridge_index, 1),
                "change_pct": round(ridge_change_pct, 2),
                "selected_alpha": float(model.alpha_),
                "rate_sensitivity_per_1pp": rate_sensitivity_per_1pp,
            },
            "live_adjustment_pp": live_adj_pp,
            "drivers": {
                "econometric": econometric_drivers,
                "live_market": live_bridge["components"],
            },
            "walk_forward_validation": {
                "oos_quarters": int(len(resids)),
                "mae_pct": round(mae_pct, 2),
                "rmse_pct": round(rmse_pct, 2),
                "naive_mean_mae_pct": round(naive_mae_pct, 2),
                "hit_rate_pct": round(hit_rate_pct, 1),
                "beats_naive_mae": bool(mae_pct < naive_mae_pct),
                "train_window": f"{feature_quarters[0]}–{feature_quarters[n_labeled - 1]}",
            },
        }

    # Build unified chart trajectory: last 16 historical quarters + 6m/12m/24m forecast fan
    hist_quarters = sorted(price_series.keys())[-16:]
    trajectory = []
    for q in hist_quarters:
        is_last = q == latest_period
        val = round(float(price_series[q]), 1)
        point: dict[str, Any] = {
            "period": q,
            "actual": val,
            "forecast": val if is_last else None,
            "econometric": val if is_last else None,
            "band_base": val if is_last else None,
            "band_width": 0.0 if is_last else None,
            "p10": val if is_last else None,
            "p90": val if is_last else None,
            "is_forecast": False,
        }
        trajectory.append(point)

    for hk in ("6m", "12m", "24m"):
        h = horizons_output[hk]
        c = h["combined"]
        trajectory.append({
            "period": h["target_period"],
            "horizon_label": hk,
            "actual": None,
            "forecast": c["forecast_index"],
            "econometric": h["econometric_ridge"]["forecast_index"],
            "band_base": c["p10_index"],
            "band_width": round(max(0.0, c["p90_index"] - c["p10_index"]), 1),
            "p10": c["p10_index"],
            "p90": c["p90_index"],
            "is_forecast": True,
        })

    return {
        "engine_version": "ridge_wf_nowcast_v1",
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "segment": segment,
        "current_period": latest_period,
        "current_index": round(latest_index, 1),
        "training_quarters": len(feature_quarters),
        "training_range": f"{feature_quarters[0]}–{latest_period}",
        "direction_12m": horizons_output["12m"]["combined"]["direction"],
        "horizons": horizons_output,
        "live_bridge": live_bridge,
        "trajectory": trajectory,
        "methodology_summary": (
            "Regulariseret Ridge-tidsseriemodel (RidgeCV) trænet på ægte kvartalsvise DST-data "
            "(EJ56 + DNRENTM, 2007–nu) kombineret med en eksplicit højfrekvent markedsjustering "
            "fra Finans Danmark (UDB020, UDB030, BM020) og Boliga API. P10–P90-båndet er "
            "beregnet direkte fra walk-forward out-of-sample fejl uden look-ahead."
        ),
    }
