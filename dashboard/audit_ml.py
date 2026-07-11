import sys
import os
import joblib
import numpy as np
import pandas as pd

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(PROJECT_ROOT, "server"))

from cph_housing_server import check_early_warnings
SEGMENTS = [
    "copenhagen_apartments",
    "copenhagen_houses",
    "frederiksberg_apartments",
    "aarhus_apartments",
    "aarhus_houses",
    "odense_apartments",
    "odense_houses",
    "aalborg_apartments",
    "aalborg_houses",
]

model_path = os.path.join(PROJECT_ROOT, "config", "ews_ml_model.joblib")
clf = joblib.load(model_path)

print("=== FEATURE IMPORTANCES ===")
importances = clf.feature_importances_
feature_names = ['ewi1_price_wage', 'ewi2_supply', 'ewi3_vol_yoy', 'ewi4_reduction', 'ewi5_dom_z', 'ewi6_p2r_z', 'ewi7_io_pct', 'ewi8_dsr']
for name, imp in zip(feature_names, importances):
    print(f"  {name}: {imp:.4f}")

print("\n=== CITY FEATURES & ML PROBABILITIES ===")
for seg in SEGMENTS:
    # Evaluate early warnings for this city
    ewi = check_early_warnings(segment=seg, ewi1_mode="yoy_expanded")
    
    # Extract features matching cph_housing_server.py line 1339
    # price_wage_spread * 100
    # months_of_supply
    # volume_yoy_change * 100
    # price_reduction_rate * 100
    # ewi5_dom_z
    # ewi6_p2r_z
    # amort_free_share * 100
    # dsr * 100
    
    # We will grab these variables by evaluating check_early_warnings internals or manually reproducing:
    # Let's inspect the returned values from check_early_warnings indicators:
    ind = ewi["indicators"]
    
    ewi1 = ind["EWI-1_price_vs_wages"]["spread_pp"]
    ewi2 = ind["EWI-2_supply_demand"]["months_of_supply"]
    ewi3 = ind["EWI-3_volume_price_divergence"]["volume_yoy_pct"]
    ewi4 = ind["EWI-4_price_reductions"]["reduction_rate_pct"]
    ewi5 = (ind["EWI-5_time_on_market"]["median_dom_days"] - ind["EWI-5_time_on_market"]["baseline_mean_days"]) / ind["EWI-5_time_on_market"]["baseline_std_days"]
    ewi6 = ind["EWI-6_price_to_rent"]["price_to_rent_ratio"] # wait, the Z-score is: (ratio - mean) / std. Let's compute it.
    
    # Wait, let's extract raw features passed in check_early_warnings:
    # Let's recreate them exactly:
    
    # Let's print out what is evaluated in check_early_warnings:
    print(f"\nSegment: {seg}")
    print(f"  Composite Score: {ewi['composite_score']}")
    print(f"  ML Probability: {ewi['ml_crash_probability']}")
    print(f"  Indicators:")
    print(f"    EWI-1 (price/wage spread): {ewi1:.2f}pp")
    print(f"    EWI-2 (months of supply): {ewi2:.2f}")
    print(f"    EWI-3 (volume YoY change): {ewi3:.2f}%")
    print(f"    EWI-4 (price reduction %): {ewi4:.2f}%")
    print(f"    EWI-5 (DOM Z-score): {ewi5:.2f} (median: {ind['EWI-5_time_on_market']['median_dom_days']})")
    # For EWI-6 Price to rent:
    p2r = ind["EWI-6_price_to_rent"]["price_to_rent_ratio"]
    p2r_mean = ind["EWI-6_price_to_rent"]["baseline_mean"]
    # We can infer std from the description string
    # Let's print the detail:
    print(f"    EWI-6 detail: {ind['EWI-6_price_to_rent']['detail']}")
    print(f"    EWI-7 (IO %): {ind['EWI-7_credit_growth']['amortization_free_share_pct']}%")
    print(f"    EWI-8 (DSR %): {ind['EWI-8_dsr']['dsr_pct']}%")
