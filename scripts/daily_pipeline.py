#!/usr/bin/env python3
"""
Copenhagen Housing Model — Daily Autonomous Pipeline
=====================================================
Scheduled to run at 02:00 AM CET daily.

Workflow:
  1. Fetch latest data via MCP tools
  2. Check all five early warning indicators
  3. Run forecast ensemble for 6, 12, and 24 months
  4. Generate dashboard data payload (consumed by React dashboard)
  5. Write summary report to artifacts

This script is designed to be invoked by the Antigravity /schedule
command or a system cron. It imports the MCP tools directly for
local execution.
"""

import sys
import json
import datetime
import os

# Add server to path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
sys.path.insert(0, os.path.join(PROJECT_ROOT, "server"))

from cph_housing_server import (
    fetch_dst_housing_data,
    calculate_user_cost,
    check_early_warnings,
    run_forecast_ensemble,
    compute_max_risk_index,
)

# ─────────────────────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────────────────────

SEGMENTS = [
    "copenhagen_apartments",
    "copenhagen_houses",
    "frederiksberg_apartments",
]

HORIZONS = [6, 12, 24]

SCENARIOS_USER_COST_PARAMS = {
    "baseline": {
        "mortgage_rate": {"6m": 0.039, "12m": 0.037, "24m": 0.035},
        "expected_appreciation": {"6m": 0.02, "12m": 0.035, "24m": 0.06},
    },
    "min_risk": {
        "mortgage_rate": {"6m": 0.035, "12m": 0.030, "24m": 0.028},
        "expected_appreciation": {"6m": 0.045, "12m": 0.09, "24m": 0.15},
    },
    "max_risk": {
        "mortgage_rate": {"6m": 0.050, "12m": 0.055, "24m": 0.060},
        "expected_appreciation": {"6m": -0.055, "12m": -0.105, "24m": -0.14},
    },
}

REF_PROPERTY_VALUE = 3_000_000  # DKK

OUTPUT_DIR = os.path.join(PROJECT_ROOT, "dashboard", "public", "data")
REPORT_DIR = os.path.join(PROJECT_ROOT, "reports")

# ─────────────────────────────────────────────────────────────
# PIPELINE
# ─────────────────────────────────────────────────────────────

def run_daily_pipeline():
    timestamp = datetime.datetime.now().isoformat()
    print(f"\n{'='*60}")
    print(f"  CPH Housing Model — Daily Pipeline")
    print(f"  {timestamp}")
    print(f"{'='*60}\n")

    # ── Step 1: Fetch latest data ──
    print("📊 Step 1: Fetching latest DST EJ56 data...")
    dst_data = fetch_dst_housing_data(table="EJ56")
    print(f"   ✅ Fetched {len(dst_data['segments'])} segments, last updated: {dst_data['last_updated']}")

    # ── Step 2: Check early warnings ──
    print("\n🚨 Step 2: Checking early warning indicators...")
    ewi_results = {}
    alert_summary = []
    for segment in SEGMENTS:
        ewi = check_early_warnings(segment=segment)
        ewi_results[segment] = ewi
        level = ewi["alert_level"]
        score = ewi["composite_score"]
        print(f"   {segment}: Score {score}/24 — {level}")
        if score >= 3:
            alert_summary.append(f"⚠️ {segment}: {level} (score {score})")

    # ── Step 3: Run forecast ensemble ──
    print("\n📈 Step 3: Running forecast ensemble...")
    forecast_results = {}
    for segment in SEGMENTS:
        forecast = run_forecast_ensemble(segment=segment, horizons=HORIZONS)
        forecast_results[segment] = forecast
        for h in HORIZONS:
            hk = f"{h}m"
            ensemble = forecast["horizons"][hk]["ensemble"]
            print(f"   {segment} [{hk}]: ensemble index {ensemble['probability_weighted_index']:.1f} "
                  f"({ensemble['probability_weighted_change_pct']:+.1f}%)")

    # ── Step 4: Calculate user costs per scenario per horizon ──
    print("\n💰 Step 4: Computing user costs...")
    user_cost_results = {}
    for scenario_name, params in SCENARIOS_USER_COST_PARAMS.items():
        user_cost_results[scenario_name] = {}
        for h in HORIZONS:
            hk = f"{h}m"
            uc = calculate_user_cost(
                property_value_dkk=REF_PROPERTY_VALUE,
                mortgage_rate=params["mortgage_rate"][hk],
                expected_appreciation=params["expected_appreciation"][hk],
                io_loan=True,
                is_couple=True,
            )
            user_cost_results[scenario_name][hk] = uc
            rate = uc["user_cost_breakdown"]["user_cost_rate"]
            monthly = uc["user_cost_breakdown"]["user_cost_monthly_dkk"]
            print(f"   {scenario_name} [{hk}]: UC rate {rate*100:.2f}%, monthly {monthly:,.0f} DKK")

    # ── Step 5: Generate dashboard data payload ──
    print("\n📦 Step 5: Generating dashboard data payload...")
    dashboard_payload = {
        "generated_at": timestamp,
        "dst_data": dst_data,
        "early_warnings": ewi_results,
        "forecasts": forecast_results,
        "user_costs": user_cost_results,
        "alerts": alert_summary,
    }

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    payload_path = os.path.join(OUTPUT_DIR, "latest_pipeline.json")
    with open(payload_path, "w") as f:
        json.dump(dashboard_payload, f, indent=2, default=str)
    print(f"   ✅ Written to {payload_path}")

    # Dynamically generate housingData.js to keep dashboard UI in sync
    js_data_path = os.path.join(PROJECT_ROOT, "dashboard", "src", "data", "housingData.js")
    
    # Extract quarters and series values
    cph_apts_data = dst_data["segments"]["copenhagen_apartments"]["series"]
    quarters = sorted(cph_apts_data.keys())
    cph_apts_list = [cph_apts_data[q] for q in quarters]
    cph_houses_list = [dst_data["segments"]["copenhagen_houses"]["series"][q] for q in quarters]
    fred_apts_list = [dst_data["segments"]["frederiksberg_apartments"]["series"][q] for q in quarters]
    
    # Early Warnings for default segment copenhagen_apartments
    ewi_cph_apts = ewi_results["copenhagen_apartments"]
    ewi_list = []
    
    indicator_mapping = {
        "EWI-1_price_vs_wages": ("EWI-1", "Price vs. Wages", "<3pp"),
        "EWI-2_supply_demand": ("EWI-2", "Supply-Demand Balance", "4.5 months"),
        "EWI-3_volume_price_divergence": ("EWI-3", "Volume-Price Divergence", "AMBER at -10%"),
        "EWI-4_price_reductions": ("EWI-4", "Price Reductions", "AMBER at >30%"),
        "EWI-5_time_on_market": ("EWI-5", "Time-on-Market", "Dynamisk Z-score"),
        "EWI-6_price_to_rent": ("EWI-6", "Price-to-Rent Ratio", "Dynamisk Z-score"),
        "EWI-7_credit_growth": ("EWI-7", "Amortization-Free Share", "<50%"),
        "EWI-8_dsr": ("EWI-8", "Debt-Servicing Ratio (DSR)", "<30%"),
    }
    
    for key, (ewi_id, ewi_name, baseline_val) in indicator_mapping.items():
        ind_data = ewi_cph_apts["indicators"][key]
        if key == "EWI-1_price_vs_wages":
            val_str = f"+{ind_data['spread_pp']:.2f}pp"
        elif key == "EWI-2_supply_demand":
            val_str = f"{ind_data['months_of_supply']:.1f} months"
        elif key == "EWI-3_volume_price_divergence":
            val_str = f"Vol {ind_data['volume_yoy_pct']:.0f}%"
        elif key == "EWI-4_price_reductions":
            val_str = f"{ind_data['reduction_rate_pct']:.0f}%"
        elif key == "EWI-5_time_on_market":
            val_str = f"{ind_data['median_dom_days']:.0f} days"
        elif key == "EWI-6_price_to_rent":
            val_str = f"{ind_data['price_to_rent_ratio']:.3f}"
        elif key == "EWI-7_credit_growth":
            val_str = f"{ind_data['amortization_free_share_pct']:.1f}%"
        elif key == "EWI-8_dsr":
            val_str = f"{ind_data['dsr_pct']:.1f}%"
            
        # Calculate indicator-specific freshness weight and latest update date
        sources = ind_data.get("data_sources", [])
        if sources:
            avg_weight = sum(s.get("freshness_weight", 1.0) for s in sources) / len(sources)
            latest_update = max(s.get("last_updated", "") for s in sources)
        else:
            avg_weight = 1.0
            latest_update = "N/A"

        ewi_list.append({
            "id": ewi_id,
            "name": ewi_name,
            "value": val_str,
            "baseline": baseline_val,
            "status": ind_data["level"],
            "description": ind_data["detail"],
            "freshness_weight": round(avg_weight, 3),
            "last_updated": latest_update
        })
        
    # Forecasts for copenhagen_apartments
    fc_cph_apts = forecast_results["copenhagen_apartments"]
    max_risk_index = compute_max_risk_index(fc_cph_apts, ewi_cph_apts)
    forecast_scenarios = []
    scenario_colors = {
        "baseline": "#00d4aa",
        "min_risk": "#3b82f6",
        "max_risk": "#ff6b6b"
    }
    scenario_labels = {
        "baseline": "Baseline",
        "min_risk": "Min Risk",
        "max_risk": "Max Risk"
    }
    
    for sc_id in ["baseline", "min_risk", "max_risk"]:
        horizon_forecasts = {}
        for h in [6, 12, 24]:
            horizon_forecasts[f"{h}m"] = fc_cph_apts["horizons"][f"{h}m"]["scenarios"][sc_id]["forecast_index"]
            
        weight = fc_cph_apts["horizons"]["12m"]["scenarios"][sc_id]["probability_weight"]
        forecast_scenarios.append({
            "scenario": scenario_labels[sc_id],
            "weight": weight,
            "color": scenario_colors[sc_id],
            "forecasts": horizon_forecasts
        })
        
    ensemble_forecasts = {
        "6m": fc_cph_apts["horizons"]["6m"]["ensemble"]["probability_weighted_index"],
        "12m": fc_cph_apts["horizons"]["12m"]["ensemble"]["probability_weighted_index"],
        "24m": fc_cph_apts["horizons"]["24m"]["ensemble"]["probability_weighted_index"]
    }
    
    ensemble_confidence_bounds = {
        "6m": fc_cph_apts["horizons"]["6m"]["ensemble"]["confidence_bounds"],
        "12m": fc_cph_apts["horizons"]["12m"]["ensemble"]["confidence_bounds"],
        "24m": fc_cph_apts["horizons"]["24m"]["ensemble"]["confidence_bounds"]
    }
    
    # User costs for 12m horizon
    user_cost_data = []
    
    for sc_id in ["baseline", "min_risk", "max_risk"]:
        uc_h = user_cost_results[sc_id]["12m"]
        rate = uc_h["user_cost_breakdown"]["user_cost_rate"]
        monthly = uc_h["user_cost_breakdown"]["user_cost_monthly_dkk"]
        assessment = uc_h["interpretation"]["assessment"]
        
        # Dynamic icon
        if rate < 0:
            icon = "⚠"
        elif rate < 0.03:
            icon = "✓"
        else:
            icon = "✗"
            
        user_cost_data.append({
            "scenario": scenario_labels[sc_id],
            "ucRate": round(rate * 100, 2),
            "monthly": int(monthly),
            "label": assessment,
            "color": scenario_colors[sc_id],
            "icon": icon
        })
        
    # Generate JS content
    js_content = f"""// AUTO-GENERATED BY DAILY PIPELINE — DO NOT EDIT DIRECTLY
const quarters = {json.dumps(quarters)};
const cphApartments = {json.dumps(cph_apts_list)};
const cphHouses = {json.dumps(cph_houses_list)};
const fredApartments = {json.dumps(fred_apts_list)};

export const priceIndexData = quarters.map((q, i) => ({{
  quarter: q,
  cphApartments: cphApartments[i],
  cphHouses: cphHouses[i],
  fredApartments: fredApartments[i],
}}));

export const earlyWarningIndicators = {json.dumps(ewi_list, indent=2)};

export const compositeScore = {ewi_cph_apts["composite_score"]};
export const freshnessWeightedComposite = {ewi_cph_apts["freshness_weighted_composite"]};
export const alertLevel = '{ewi_cph_apts["alert_level"]}';

export const dataFreshness = {json.dumps(ewi_cph_apts["data_freshness_summary"], indent=2)};

export const maxRiskIndex = {json.dumps(max_risk_index, indent=2)};

export const forecastScenarios = {json.dumps(forecast_scenarios, indent=2)};

export const ensembleForecasts = {json.dumps(ensemble_forecasts, indent=2)};
export const ensembleConfidenceBounds = {json.dumps(ensemble_confidence_bounds, indent=2)};

export const forecastBarData = ['6m', '12m', '24m'].map((horizon) => ({{
  horizon,
  Baseline: forecastScenarios[0].forecasts[horizon],
  'Min Risk': forecastScenarios[1].forecasts[horizon],
  'Max Risk': forecastScenarios[2].forecasts[horizon],
  Ensemble: ensembleForecasts[horizon],
}}));

export const userCostData = {json.dumps(user_cost_data, indent=2)};

export const scenarioAssumptions = [
  {{
    scenario: 'Baseline',
    weight: '55%',
    color: '#00d4aa',
    assumptions: {{
      'Mortgage Rate (30Y Fixed)': '3.7% → 3.5%',
      'ECB Deposit Rate Path': '2.75% → 2.0%',
      'Wage Growth (Nominal YoY)': '3.5%',
      'Expected Appreciation': '+2.0% → +6.0%',
      'Net Migration (CPH)': '+8,500/yr',
      'Completions Pipeline (12m)': '3,500 units',
      'Rentefradrag': '33%',
    }},
  }},
  {{
    scenario: 'Min Risk',
    weight: '20%',
    color: '#3b82f6',
    assumptions: {{
      'Mortgage Rate (30Y Fixed)': '3.5% → 2.8%',
      'ECB Deposit Rate Path': '2.75% → 1.0%',
      'Wage Growth (Nominal YoY)': '4.5%',
      'Expected Appreciation': '+4.5% → +15.0%',
      'Net Migration (CPH)': '+11,000/yr',
      'Completions Pipeline (12m)': '2,800 units (delayed)',
      'Rentefradrag': '33%',
    }},
  }},
  {{
    scenario: 'Max Risk',
    weight: '25%',
    color: '#ff6b6b',
    assumptions: {{
      'Mortgage Rate (30Y Fixed)': '5.0% → 6.0%',
      'ECB Deposit Rate Path': '2.75% → 4.25%',
      'Wage Growth (Nominal YoY)': '2.5% (below inflation)',
      'Expected Appreciation': '-5.5% → -14.0%',
      'Net Migration (CPH)': '+4,000/yr',
      'Completions Pipeline (12m)': '5,500 units (supply glut)',
      'Rentefradrag': '25% (reduced)',
    }},
  }},
];
"""
    with open(js_data_path, "w") as f:
        f.write(js_content)
    print(f"   ✅ Written to {js_data_path}")

    # ── Step 6: Generate daily report ──
    print("\n📝 Step 6: Generating daily report...")
    os.makedirs(REPORT_DIR, exist_ok=True)
    date_str = datetime.datetime.now().strftime("%Y-%m-%d")
    report_path = os.path.join(REPORT_DIR, f"daily_{date_str}.md")

    report = generate_daily_report(dst_data, ewi_results, forecast_results, user_cost_results, alert_summary)
    with open(report_path, "w") as f:
        f.write(report)
    print(f"   ✅ Written to {report_path}")

    # ── Summary ──
    print(f"\n{'='*60}")
    print(f"  Pipeline complete at {datetime.datetime.now().isoformat()}")
    if alert_summary:
        print(f"  ⚠️  ALERTS: {len(alert_summary)}")
        for a in alert_summary:
            print(f"     {a}")
    else:
        print(f"  ✅ No alerts. All segments NORMAL.")
    print(f"{'='*60}\n")

    return dashboard_payload


def generate_daily_report(dst_data, ewi_results, forecast_results, user_cost_results, alerts):
    """Generate a markdown daily report."""
    now = datetime.datetime.now()
    lines = [
        f"# CPH Housing Model — Daily Report",
        f"> **Date**: {now.strftime('%Y-%m-%d')}  ",
        f"> **Generated**: {now.isoformat()}  ",
        "",
        "## Early Warning Status",
        "",
        "| Segment | Score | Alert Level | Flagged Indicators |",
        "|---|---|---|---|",
    ]

    for seg, ewi in ewi_results.items():
        flagged = [
            f"{k}: {v['level']}"
            for k, v in ewi["indicators"].items()
            if v["level"] != "GREEN"
        ]
        flagged_str = ", ".join(flagged) if flagged else "None"
        lines.append(f"| {seg} | {ewi['composite_score']}/24 | {ewi['alert_level']} | {flagged_str} |")

    lines.extend(["", "## Forecast Ensemble (Probability-Weighted)", ""])
    lines.append("| Segment | 6m | 12m | 24m |")
    lines.append("|---|---|---|---|")

    for seg, forecast in forecast_results.items():
        vals = []
        for h in [6, 12, 24]:
            hk = f"{h}m"
            e = forecast["horizons"][hk]["ensemble"]
            vals.append(f"{e['probability_weighted_index']:.1f} ({e['probability_weighted_change_pct']:+.1f}%)")
        lines.append(f"| {seg} | {' | '.join(vals)} |")

    lines.extend(["", "## User Cost (12m Horizon, 3M DKK Reference)", ""])
    lines.append("| Scenario | UC Rate | Monthly (DKK) | Assessment |")
    lines.append("|---|---|---|---|")

    for scenario, horizons in user_cost_results.items():
        uc = horizons["12m"]
        rate = uc["user_cost_breakdown"]["user_cost_rate"]
        monthly = uc["user_cost_breakdown"]["user_cost_monthly_dkk"]
        assessment = uc["interpretation"]["assessment"]
        lines.append(f"| {scenario} | {rate*100:.2f}% | {monthly:,.0f} | {assessment} |")

    if alerts:
        lines.extend(["", "## ⚠️ Active Alerts", ""])
        for a in alerts:
            lines.append(f"- {a}")

    return "\n".join(lines)


if __name__ == "__main__":
    run_daily_pipeline()
