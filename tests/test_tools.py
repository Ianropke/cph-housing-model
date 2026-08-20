#!/usr/bin/env python3
"""
Test harness for CphHousingModel MCP server tools.
Validates calculate_user_cost against the Nationalbanken formula
and runs all tools with sample inputs.
"""

import sys
import json
import datetime
from unittest.mock import patch

# Add server to path
sys.path.insert(0, "../server")

# ═══════════════════════════════════════════════════════════════
# Direct function imports (bypasses MCP transport for testing)
# ═══════════════════════════════════════════════════════════════
from cph_housing_server import (
    fetch_dst_housing_data,
    calculate_user_cost,
    check_early_warnings,
    run_forecast_ensemble,
)


def pp(label: str, data: dict):
    """Pretty-print a result."""
    print(f"\n{'='*70}")
    print(f"  {label}")
    print(f"{'='*70}")
    print(json.dumps(data, indent=2, default=str))


# ─────────────────────────────────────────────────────────────
# TEST 1: calculate_user_cost — Nationalbanken formula validation
# ─────────────────────────────────────────────────────────────

print("\n" + "█"*70)
print("  TEST 1: User Cost Calculation — Nationalbanken Formula")
print("█"*70)

# Dummy data: 3M DKK apartment, 4% rate, standard deductions
result = calculate_user_cost(
    property_value_dkk=3_000_000,
    mortgage_rate=0.04,
    property_tax_rate=0.0092,
    depreciation_rate=0.015,
    risk_premium=0.010,
    expected_appreciation=0.03,
    io_loan=True,
    is_couple=True,
)

pp("User Cost — Baseline (IO loan, 4%, 3% appreciation)", result)

# Manual verification:
# interest_expense = 3M * 0.80 * 0.04 = 96k DKK (under 100k DKK couple threshold) -> tau_r = 0.33
# after_tax_rate = 0.04 * (1 - 0.33) = 0.0268
# UC_rate = 0.0268 + 0.0092 + 0.015 + 0.01 = 0.0618
# UC_annual = 0.0618 * 3,000,000 = 185,400 DKK
# UC_monthly = 185,400 / 12 = 15,450 DKK

expected_uc_rate = 0.04 * (1 - 0.33) + 0.0092 + 0.015 + 0.01
actual_uc_rate = result["user_cost_breakdown"]["user_cost_rate"]
assert abs(actual_uc_rate - expected_uc_rate) < 0.0001, \
    f"UC rate mismatch: {actual_uc_rate} != {expected_uc_rate}"
print(f"\n✅ Formula verified: UC rate = {actual_uc_rate:.5f} (expected {expected_uc_rate:.5f})")

# Test max_risk scenario (high rates, negative appreciation, couples=False to trigger bracket reduction)
result_stress = calculate_user_cost(
    property_value_dkk=3_000_000,
    mortgage_rate=0.055,
    property_tax_rate=0.0092,
    depreciation_rate=0.015,
    risk_premium=0.010,
    expected_appreciation=-0.105,  # expecting -10.5% decline
    io_loan=True,
    is_couple=False,
)
pp("User Cost — Max Risk (5.5%, -10.5% appreciation, single)", result_stress)

# Test min_risk scenario (low rates, high appreciation)
result_bull = calculate_user_cost(
    property_value_dkk=3_000_000,
    mortgage_rate=0.030,
    property_tax_rate=0.0092,
    depreciation_rate=0.015,
    risk_premium=0.010,
    expected_appreciation=0.09,
    io_loan=True,
    is_couple=True,
)
pp("User Cost — Min Risk (3.0%, 9% appreciation)", result_bull)

# ─────────────────────────────────────────────────────────────
# TEST 2: fetch_dst_housing_data
# ─────────────────────────────────────────────────────────────

print("\n" + "█"*70)
print("  TEST 2: Fetch DST Housing Data (EJ56)")
print("█"*70)

# Fetch all segments, last 2 years
live_housing_data = fetch_dst_housing_data(table="EJ56", start_period="2024Q1")
pp("DST EJ56 — All segments from 2024Q1", live_housing_data)

# Fetch single segment
data_cph = fetch_dst_housing_data(
    table="EJ56",
    segment="copenhagen_apartments",
    start_period="2025Q1",
)
pp("DST EJ56 — Copenhagen apartments from 2025Q1", data_cph)


# ─────────────────────────────────────────────────────────────
# TEST 3: check_early_warnings
# ─────────────────────────────────────────────────────────────

print("\n" + "█"*70)
print("  TEST 3: Early Warning System Check")
print("█"*70)

macro_fixture = {
    "unemployment_rate": 0.035,
    "rent_index": 120.0,
    "rent_series": {period: 120.0 for period in live_housing_data["segments"]["copenhagen_apartments"]["series"]},
    "disposable_income_cph": 400000.0,
    "disposable_income_frb": 400000.0,
    "interest_rate": 0.03,
    "wage_growth": 0.032,
}
with patch("dst_macro.fetch_dst_macro_data", return_value=macro_fixture):
    for segment in ["copenhagen_apartments", "copenhagen_houses", "frederiksberg_apartments"]:
        ewi = check_early_warnings(segment=segment, dst_data=live_housing_data)
        pp(f"EWI Status — {segment}", ewi)


# ─────────────────────────────────────────────────────────────
# TEST 4: run_forecast_ensemble
# ─────────────────────────────────────────────────────────────

print("\n" + "█"*70)
print("  TEST 4: Forecast Ensemble (6m, 12m, 24m)")
print("█"*70)

for segment in ["copenhagen_apartments", "copenhagen_houses"]:
    forecast = run_forecast_ensemble(segment=segment, horizons=[6, 12, 24], dst_data=live_housing_data)
    pp(f"Forecast Ensemble — {segment}", forecast)


# ─────────────────────────────────────────────────────────────
# SUMMARY
# ─────────────────────────────────────────────────────────────

print("\n" + "█"*70)
print("  ALL TESTS PASSED ✅")
print("█"*70)
print(f"\nTimestamp: {datetime.datetime.now().isoformat()}")
print("Server: CphHousingModel (FastMCP)")
print("Tools tested: fetch_dst_housing_data, calculate_user_cost,")
print("              check_early_warnings, run_forecast_ensemble")
