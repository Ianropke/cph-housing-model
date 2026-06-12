#!/usr/bin/env python3
"""
Comprehensive test suite for verifying the economic logic of the
Copenhagen Housing Market Model.

Tests:
  - User Cost formula correctness (including property tax)
  - Tax bracket boundary conditions
  - Forecast ensemble includes property tax
  - Credit shock avoids double-counting
  - Monte Carlo stochastic variation
  - Scenario probability weights sum to 1.0
  - Composite EWI score bounds
  - Edge cases (zero value, extreme rates)
"""

import sys
import math
import unittest

sys.path.insert(0, "../server")

from cph_housing_server import (
    calculate_user_cost,
    check_early_warnings,
    run_forecast_ensemble,
    SCENARIOS,
    DST_EJ56_DATA,
)


class TestUserCostFormula(unittest.TestCase):
    """Verify the UC = P × [r(1-τ_r) + τ_p + δ + rp - π_e] formula."""

    def test_baseline_manual_calculation(self):
        """Hand-calculated UC for a 3M DKK apartment, couple, 4% rate."""
        result = calculate_user_cost(
            property_value_dkk=3_000_000,
            mortgage_rate=0.04,
            property_tax_rate=0.0092,
            depreciation_rate=0.015,
            risk_premium=0.010,
            expected_appreciation=0.03,
            is_couple=True,
        )

        # Manual: debt = 2.4M, interest = 96k DKK < 100k threshold → τ_r = 0.33
        # after_tax_rate = 0.04 × (1 - 0.33) = 0.0268
        # uc_rate = 0.0268 + 0.0092 + 0.015 + 0.010 - 0.03 = 0.031
        expected_uc_rate = 0.04 * (1 - 0.33) + 0.0092 + 0.015 + 0.010 - 0.03

        self.assertAlmostEqual(
            result["user_cost_breakdown"]["user_cost_rate"],
            expected_uc_rate,
            places=4,
            msg="User cost rate does not match hand calculation",
        )

        # Annual UC = rate × P
        expected_annual = expected_uc_rate * 3_000_000
        self.assertAlmostEqual(
            result["user_cost_breakdown"]["user_cost_annual_dkk"],
            expected_annual,
            places=0,
        )

    def test_formula_string_includes_rp(self):
        """The displayed formula string must include the risk premium term."""
        result = calculate_user_cost(
            property_value_dkk=3_000_000,
            mortgage_rate=0.04,
        )
        formula = result.get("formula", "")
        self.assertIn("rp", formula, "Formula string is missing 'rp' (risk premium)")
        self.assertNotIn(
            "expected_appreciation",
            formula,
            "Formula string uses verbose var name instead of pi_e",
        )


class TestTaxBracketBoundaries(unittest.TestCase):
    """Verify rentefradrag bracket transitions at 50k/100k DKK thresholds."""

    def test_single_below_threshold(self):
        """Single buyer with interest < 50k DKK → full 33% deduction."""
        # P = 1M, rate = 0.05 → interest = 1M × 0.8 × 0.05 = 40k < 50k ✓
        result = calculate_user_cost(
            property_value_dkk=1_000_000,
            mortgage_rate=0.05,
            is_couple=False,
        )
        self.assertAlmostEqual(
            result["user_cost_breakdown"]["effective_tax_deduction_rate"], 0.33, places=4
        )

    def test_single_above_threshold(self):
        """Single buyer with interest > 50k DKK → blended rate < 33%."""
        # P = 3M, rate = 0.05 → interest = 3M × 0.8 × 0.05 = 120k > 50k
        result = calculate_user_cost(
            property_value_dkk=3_000_000,
            mortgage_rate=0.05,
            is_couple=False,
        )
        eff = result["user_cost_breakdown"]["effective_tax_deduction_rate"]
        # Blended: (50k × 0.33 + 70k × 0.25) / 120k = 0.2833
        expected = (50_000 * 0.33 + 70_000 * 0.25) / 120_000
        self.assertAlmostEqual(eff, expected, places=4)
        self.assertLess(eff, 0.33, "Effective rate should be below 33% above threshold")
        self.assertGreater(eff, 0.25, "Effective rate should be above 25% (floor)")

    def test_couple_higher_threshold(self):
        """Couple with interest 80k DKK → below 100k threshold → full 33%."""
        # P = 2M, rate = 0.05 → interest = 2M × 0.8 × 0.05 = 80k < 100k ✓
        result = calculate_user_cost(
            property_value_dkk=2_000_000,
            mortgage_rate=0.05,
            is_couple=True,
        )
        self.assertAlmostEqual(
            result["user_cost_breakdown"]["effective_tax_deduction_rate"], 0.33, places=4
        )

    def test_couple_above_threshold(self):
        """Couple with interest > 100k DKK → blended rate."""
        # P = 5M, rate = 0.05 → interest = 5M × 0.8 × 0.05 = 200k > 100k
        result = calculate_user_cost(
            property_value_dkk=5_000_000,
            mortgage_rate=0.05,
            is_couple=True,
        )
        eff = result["user_cost_breakdown"]["effective_tax_deduction_rate"]
        expected = (100_000 * 0.33 + 100_000 * 0.25) / 200_000
        self.assertAlmostEqual(eff, expected, places=4)


class TestScenarioProbabilities(unittest.TestCase):
    """Verify scenario weights are valid."""

    def test_weights_sum_to_one(self):
        total = sum(s["probability_weight"] for s in SCENARIOS.values())
        self.assertAlmostEqual(total, 1.0, places=6, msg="Scenario weights must sum to 1.0")

    def test_all_weights_positive(self):
        for name, s in SCENARIOS.items():
            self.assertGreater(
                s["probability_weight"], 0, f"Scenario '{name}' has non-positive weight"
            )


class TestForecastEnsembleUC(unittest.TestCase):
    """Verify the forecast ensemble includes property tax in UC."""

    def test_ensemble_uc_includes_property_tax(self):
        """UC rate in forecast must exceed the sum of components WITHOUT property tax."""
        result = run_forecast_ensemble(segment="copenhagen_apartments", horizons=[12])
        horizon_data = result["horizons"]["12m"]

        for scenario_id, scenario_result in horizon_data["scenarios"].items():
            scenario = SCENARIOS[scenario_id]
            rate_12m = scenario["mortgage_rate"]["12m"]
            rentefradrag = scenario["rentefradrag"]

            # The reported UC rate must include property_tax (~0.0092)
            after_tax_rate = rate_12m * (1 - rentefradrag)
            uc_without_tax = after_tax_rate + scenario["depreciation"] + scenario["risk_premium"]
            reported_uc = scenario_result["user_cost_rate"]
            appreciation = scenario_result["annualised_return_pct"] / 100

            # UC + appreciation should be > uc_without_tax + property_tax margin
            uc_plus_appreciation = reported_uc + appreciation
            self.assertGreater(
                uc_plus_appreciation,
                uc_without_tax + 0.005,
                f"Scenario '{scenario_id}' UC appears to be missing property tax",
            )


class TestCreditShockNoDoubleCounting(unittest.TestCase):
    """Verify credit shock uses scenario-implied rate, not a global baseline."""

    def test_6m_no_shock_applied(self):
        """At 6-month horizon, rate == scenario's 6m rate, so shock should be ~zero."""
        result = run_forecast_ensemble(segment="copenhagen_apartments", horizons=[6])
        horizon_data = result["horizons"]["6m"]

        for scenario_id, scenario_result in horizon_data["scenarios"].items():
            scenario = SCENARIOS[scenario_id]
            expected_appr = scenario["expected_appreciation"]["6m"]
            annualised = scenario_result["annualised_return_pct"] / 100

            # At 6m, rate = scenario's 6m rate, so rate_shock ≈ 0
            self.assertAlmostEqual(
                annualised,
                expected_appr,
                places=3,
                msg=f"Scenario '{scenario_id}' 6m: annualised return {annualised} "
                    f"diverges from expected {expected_appr} — possible double-counting",
            )

    def test_max_risk_12m_not_extreme(self):
        """Max Risk 12m should NOT produce -19.5% (the old double-counted value)."""
        result = run_forecast_ensemble(segment="copenhagen_apartments", horizons=[12])
        max_risk = result["horizons"]["12m"]["scenarios"]["max_risk"]
        annualised = max_risk["annualised_return_pct"]

        # Old bug produced ~ -19.5%. Fixed value should be closer to -10.5% to -15%
        self.assertGreater(
            annualised,
            -18.0,
            f"Max Risk 12m annualised return is {annualised}% — still looks double-counted!",
        )


class TestCompositeEWI(unittest.TestCase):
    """Verify EWI composite score is correctly bounded."""

    def test_composite_score_within_bounds(self):
        for segment in ["copenhagen_apartments", "copenhagen_houses", "frederiksberg_apartments"]:
            result = check_early_warnings(segment)
            score = result["composite_score"]
            self.assertGreaterEqual(score, 0, f"Score below 0 for {segment}")
            self.assertLessEqual(score, 21, f"Score above 21 for {segment}")

    def test_all_indicators_present(self):
        result = check_early_warnings("copenhagen_apartments")
        indicators = result["indicators"]
        for ewi_key in [
            "EWI-1_price_vs_wages",
            "EWI-2_supply_demand",
            "EWI-3_volume_price_divergence",
            "EWI-4_price_reductions",
            "EWI-5_time_on_market",
            "EWI-6_price_to_rent",
            "EWI-7_credit_growth",
        ]:
            self.assertIn(ewi_key, indicators, f"Missing indicator {ewi_key}")

    def test_valid_statuses(self):
        result = check_early_warnings("copenhagen_apartments")
        valid = {"GREEN", "AMBER", "RED"}
        for ewi_key, ind in result["indicators"].items():
            self.assertIn(
                ind["level"], valid, f"{ewi_key} has invalid status: {ind['level']}"
            )

    def test_ewi1_modes(self):
        """Verify that the 4 modes for EWI-1 compute different statuses and spreads."""
        # Test Copenhagen apartments
        res_yoy_orig = check_early_warnings("copenhagen_apartments", ewi1_mode="yoy_original")
        res_yoy_exp = check_early_warnings("copenhagen_apartments", ewi1_mode="yoy_expanded")
        res_struct_3y = check_early_warnings("copenhagen_apartments", ewi1_mode="structural_3y")
        res_struct_5y = check_early_warnings("copenhagen_apartments", ewi1_mode="structural_5y")

        # All 4 should have EWI-1 modes dict
        ewi1_orig = res_yoy_orig["indicators"]["EWI-1_price_vs_wages"]
        self.assertIn("modes", ewi1_orig)
        
        # Check active level values
        self.assertEqual(ewi1_orig["level"], "RED")
        self.assertEqual(res_yoy_exp["indicators"]["EWI-1_price_vs_wages"]["level"], "RED")
        self.assertEqual(res_struct_3y["indicators"]["EWI-1_price_vs_wages"]["level"], "AMBER")
        self.assertEqual(res_struct_5y["indicators"]["EWI-1_price_vs_wages"]["level"], "AMBER")

        # Test Copenhagen houses (should be GREEN under 3y MA)
        res_houses_3y = check_early_warnings("copenhagen_houses", ewi1_mode="structural_3y")
        self.assertEqual(res_houses_3y["indicators"]["EWI-1_price_vs_wages"]["level"], "GREEN")


class TestMonteCarloVariation(unittest.TestCase):
    """Verify Monte Carlo actually produces a spread of values."""

    def test_confidence_interval_spread(self):
        """p10 and p90 should differ meaningfully (not zero variance)."""
        result = run_forecast_ensemble(segment="copenhagen_apartments", horizons=[12])
        mc = result["horizons"]["12m"]["ensemble"]["confidence_bounds"]
        p10 = mc["p10"]
        p90 = mc["p90"]
        spread = p90 - p10
        self.assertGreater(spread, 1.0, f"MC spread is only {spread} — too narrow")
        self.assertLess(spread, 50.0, f"MC spread is {spread} — unrealistically wide")

    def test_p50_near_ensemble(self):
        """Median should be close to the deterministic ensemble."""
        result = run_forecast_ensemble(segment="copenhagen_apartments", horizons=[12])
        ensemble_idx = result["horizons"]["12m"]["ensemble"]["probability_weighted_index"]
        mc = result["horizons"]["12m"]["ensemble"]["confidence_bounds"]
        p50 = mc["p50"]
        self.assertAlmostEqual(ensemble_idx, p50, delta=3.0)


class TestEdgeCases(unittest.TestCase):
    """Boundary and edge case validation."""

    def test_zero_property_value(self):
        """Zero property value should produce zero costs."""
        result = calculate_user_cost(property_value_dkk=0, mortgage_rate=0.04)
        self.assertEqual(result["user_cost_breakdown"]["user_cost_annual_dkk"], 0)
        self.assertEqual(result["user_cost_breakdown"]["user_cost_monthly_dkk"], 0)

    def test_zero_mortgage_rate(self):
        """Zero rate should still produce costs from property tax, depreciation, and rp."""
        result = calculate_user_cost(
            property_value_dkk=3_000_000,
            mortgage_rate=0.0,
        )
        uc_rate = result["user_cost_breakdown"]["user_cost_rate"]
        # Should be > 0 because of property_tax (0.0092) + depreciation (0.015) + rp (0.01)
        self.assertGreater(uc_rate, 0.03, "UC should be positive even with 0% mortgage rate")

    def test_high_appreciation_negative_uc(self):
        """Very high expected appreciation should produce negative UC."""
        result = calculate_user_cost(
            property_value_dkk=3_000_000,
            mortgage_rate=0.04,
            expected_appreciation=0.15,
        )
        uc_rate = result["user_cost_breakdown"]["user_cost_rate"]
        self.assertLess(uc_rate, 0, "UC should be negative with 15% expected appreciation")


class TestDSTDataPlausibility(unittest.TestCase):
    """Verify DST EJ56 data is internally consistent and plausible."""

    def test_all_segments_have_latest_data(self):
        for seg_id, seg in DST_EJ56_DATA["segments"].items():
            periods = sorted(seg["series"].keys())
            self.assertIn("2025Q4", periods, f"Segment {seg_id} missing 2025Q4")

    def test_index_values_in_plausible_range(self):
        """All index values should be between 50 and 300 (2006=100 base)."""
        for seg_id, seg in DST_EJ56_DATA["segments"].items():
            for period, value in seg["series"].items():
                self.assertGreater(value, 50, f"{seg_id} {period}: index {value} too low")
                self.assertLess(value, 300, f"{seg_id} {period}: index {value} too high")

    def test_segments_correlated(self):
        """CPH apartments and Frederiksberg apartments should move in similar directions."""
        cph = DST_EJ56_DATA["segments"]["copenhagen_apartments"]["series"]
        frb = DST_EJ56_DATA["segments"]["frederiksberg_apartments"]["series"]
        common_periods = sorted(set(cph.keys()) & set(frb.keys()))

        for period in common_periods:
            ratio = cph[period] / frb[period]
            self.assertGreater(ratio, 0.8, f"{period}: CPH/FRB ratio {ratio} too low")
            self.assertLess(ratio, 1.2, f"{period}: CPH/FRB ratio {ratio} too high")


if __name__ == "__main__":
    unittest.main(verbosity=2)
