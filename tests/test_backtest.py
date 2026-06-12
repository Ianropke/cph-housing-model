#!/usr/bin/env python3
"""
Test harness for CphHousingModel MCP server run_historical_backtest tool.
Validates backtesting accuracy and output structure.
"""

import sys
import json
import datetime

# Add server to path
sys.path.insert(0, "../server")

from cph_housing_server import run_historical_backtest


def pp(label: str, data: dict):
    """Pretty-print a result."""
    print(f"\n{'='*70}")
    print(f"  {label}")
    print(f"{'='*70}")
    print(json.dumps(data, indent=2, default=str))


print("\n" + "█"*70)
print("  TEST: Historical Backtesting Tool")
print("█"*70)

# Run standard backtest
result = run_historical_backtest(start_year=2007, end_year=2024)
pp("Backtest Results (2007 - 2024)", result)

# Assertions
assert "metrics" in result, "Missing 'metrics' key in backtest results"
assert "empirical_calibrations" in result, "Missing 'empirical_calibrations' key"
assert "comparison" in result, "Missing 'comparison' key"

metrics = result["metrics"]
assert "mape_pct" in metrics, "Missing 'mape_pct' in metrics"
assert "rmse_points" in metrics, "Missing 'rmse_points' in metrics"
assert metrics["data_points_evaluated"] == 17, f"Expected 17 data points, got {metrics['data_points_evaluated']}"

calibrations = result["empirical_calibrations"]
assert "EWI-1_price_vs_wages_red" in calibrations, "Missing EWI-1 calibration"
assert "EWI-2_supply_demand_amber" in calibrations, "Missing EWI-2 calibration"
assert "EWI-6_price_to_rent_red_ratio" in calibrations, "Missing EWI-6 calibration"

print("\n✅ Backtest structure and assertions verified successfully!")

# Test invalid bounds
print("\nTesting validation of invalid bounds...")
invalid_result = run_historical_backtest(start_year=2025, end_year=2020)
assert "error" in invalid_result, "Expected error for invalid year range"
print("✅ Invalid bounds correctly handled: ", invalid_result["error"])

print("\n" + "█"*70)
print("  BACKTEST TESTS PASSED ✅")
print("█"*70)
