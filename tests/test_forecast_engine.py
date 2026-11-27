#!/usr/bin/env python3
"""Unit and walk-forward integrity tests for server/forecast_engine.py."""
from __future__ import annotations

import math
import unittest

from forecast_engine import run_data_driven_forecast


def _synthetic_series(n: int = 60, rate_shift: float = 0.0):
    """Build deterministic quarterly price & rate series (for unit testing only)."""
    prices = {}
    rates = {}
    p = 100.0
    for i in range(n):
        year = 2010 + (i // 4)
        q = (i % 4) + 1
        key = f"{year}Q{q}"
        r = 0.02 + 0.015 * math.sin(i / 6.0) + (rate_shift if i >= n - 4 else 0.0)
        growth = 0.012 - 0.35 * (r - 0.02) + 0.004 * math.cos(i / 3.0)
        p = p * (1.0 + growth)
        prices[key] = round(p, 2)
        rates[key] = round(r, 4)
    return prices, rates


class TestForecastEngine(unittest.TestCase):
    def test_walk_forward_bounds_and_driver_structure(self):
        prices, rates = _synthetic_series(60)
        res = run_data_driven_forecast(
            "copenhagen_apartments",
            prices,
            rates,
            segment_nowcast={"rkr_udb020": {"since_dst_quarter_change_pct": -2.0}},
            segment_market={"median_dom": 80, "price_reduction_rate": 0.42, "volume_yoy_change": -0.18},
        )
        self.assertEqual(res["segment"], "copenhagen_apartments")
        self.assertIn(res["direction_12m"], ("OP", "FLADT", "NED"))
        for hk in ("6m", "12m", "24m"):
            h = res["horizons"][hk]
            c = h["combined"]
            self.assertLessEqual(c["p10_index"], c["p50_index"])
            self.assertLessEqual(c["p50_index"], c["p90_index"])
            self.assertGreater(h["walk_forward_validation"]["oos_quarters"], 10)
            self.assertGreater(len(h["drivers"]["econometric"]), 3)
            self.assertGreater(len(h["drivers"]["live_market"]), 2)
            self.assertLess(h["live_adjustment_pp"], 0.0)

    def test_negative_nowcast_reduces_combined_forecast(self):
        prices, rates = _synthetic_series(60)
        neutral = run_data_driven_forecast(
            "copenhagen_apartments",
            prices,
            rates,
            segment_nowcast={"rkr_udb020": {"since_dst_quarter_change_pct": 0.0}},
            segment_market={"median_dom": 55, "price_reduction_rate": 0.25, "volume_yoy_change": 0.05},
        )
        bearish = run_data_driven_forecast(
            "copenhagen_apartments",
            prices,
            rates,
            segment_nowcast={"rkr_udb020": {"since_dst_quarter_change_pct": -4.0}},
            segment_market={"median_dom": 95, "price_reduction_rate": 0.50, "volume_yoy_change": -0.25},
        )
        for hk in ("6m", "12m", "24m"):
            self.assertLess(
                bearish["horizons"][hk]["combined"]["change_pct"],
                neutral["horizons"][hk]["combined"]["change_pct"],
            )

    def test_insufficient_history_raises(self):
        prices, rates = _synthetic_series(12)
        with self.assertRaises(ValueError):
            run_data_driven_forecast("copenhagen_apartments", prices, rates)


if __name__ == "__main__":
    unittest.main()
