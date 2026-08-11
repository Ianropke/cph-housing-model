#!/usr/bin/env python3
"""Build the market-input payload from live, attributable source data only."""

import datetime as dt
import json
import os
import re
import statistics
import sys
import time

from curl_cffi import requests

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(PROJECT_ROOT, "server"))
from rkr_statbank import fetch_scalar


SEGMENTS = {
    "copenhagen_apartments": {"area": "101", "category": "2", "property_type": 3, "zip_from": 1000, "zip_to": 2999},
    "copenhagen_houses": {"area": "101", "category": "1", "property_type": 1, "zip_from": 1000, "zip_to": 2999},
    "frederiksberg_apartments": {"area": "147", "category": "2", "property_type": 3, "zip_from": 2000, "zip_to": 2000},
}


def fetch_boliga_reductions(property_type: int, zip_from: int, zip_to: int) -> dict:
    """Fetch active listings from Boliga. Failure is fatal: there is no fallback."""
    listings, page = [], 1
    while True:
        url = (
            "https://api.boliga.dk/api/v2/search/results?"
            f"pageSize=500&page={page}&propertyType={property_type}"
            f"&zipcodeFrom={zip_from}&zipcodeTo={zip_to}"
        )
        response = None
        for attempt in range(3):
            try:
                candidate = requests.get(url, impersonate="chrome110", timeout=20)
                if candidate.status_code == 200:
                    response = candidate
                    break
                print(f"Boliga returned {candidate.status_code}; retry {attempt + 1}/3")
            except Exception as error:
                print(f"Boliga request error; retry {attempt + 1}/3: {error}")
            time.sleep(2)
        if response is None:
            raise RuntimeError(f"Boliga did not return live data for property type {property_type}")

        payload = response.json()
        results = payload.get("results")
        if not isinstance(results, list):
            raise RuntimeError("Boliga response has no results list")
        listings.extend(results)
        if page >= payload.get("meta", {}).get("totalPages", 1):
            break
        page += 1
        time.sleep(0.5)

    if not listings:
        raise RuntimeError(f"Boliga returned zero active listings for property type {property_type}")
    changes = [item["priceChangePercentTotal"] for item in listings if item.get("priceChangePercentTotal") is not None]
    reductions = [abs(value) for value in changes if value < 0]
    return {
        "price_reduction_rate": round(len(reductions) / len(listings), 3),
        "avg_reduction_magnitude": round(statistics.mean(reductions) / 100, 3) if reductions else 0.0,
        "listings_sample_size": len(listings),
        "status": "live",
        "source": "Boliga API",
        "retrieved_at": dt.datetime.now(dt.timezone.utc).isoformat(),
    }


def previous_year(period: str) -> str:
    match = re.fullmatch(r"(\d{4})K([1-4])", period)
    if not match:
        raise ValueError(f"Expected RKR quarterly period, got {period!r}")
    return f"{int(match.group(1)) - 1}K{match.group(2)}"


def rkr_segment_metrics(area: str, category: str) -> dict:
    listings = fetch_scalar("UDB010", {1: area, 2: category, 3: "6"})
    days_on_market = fetch_scalar("UDB030", {1: area, 2: category, 3: "9"})
    sales = fetch_scalar("BM020", {1: area, 2: category, 3: "SALG"})
    sales_last_year = fetch_scalar("BM020", {1: area, 2: category, 3: "SALG"}, previous_year(sales["period"]))
    if sales["value"] <= 0 or sales_last_year["value"] <= 0:
        raise RuntimeError(f"RKR sales data is not usable for area {area}, category {category}")
    return {
        "months_of_supply": round(listings["value"] / (sales["value"] / 3), 2),
        "volume_yoy_change": round((sales["value"] / sales_last_year["value"]) - 1, 4),
        "median_dom": int(days_on_market["value"]),
        "rkr_observations": {
            "active_listings": listings,
            "days_on_market": days_on_market,
            "sales_latest_quarter": sales,
            "sales_same_quarter_last_year": sales_last_year,
        },
    }


def rkr_interest_only_share() -> dict:
    interest_only = fetch_scalar("UL30", {1: "A", 2: "1", 3: "33", 4: "111"})
    total = fetch_scalar("UL30", {1: "A", 2: "0", 3: "33", 4: "111"}, interest_only["period"])
    if total["value"] <= 0:
        raise RuntimeError("RKR UL30 total lending is zero")
    return {
        "share": round(interest_only["value"] / total["value"], 4),
        "observations": {"interest_only": interest_only, "total": total},
    }


def fetch_market_data() -> dict:
    interest_only = rkr_interest_only_share()
    data = {
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "last_updated": dt.date.today().isoformat(),
        "source_status": "live",
        "sources": {
            "rkr": "Finans Danmark Statistikbank",
            "boliga": "Boliga API",
        },
    }
    for segment, spec in SEGMENTS.items():
        boliga = fetch_boliga_reductions(spec["property_type"], spec["zip_from"], spec["zip_to"])
        rkr = rkr_segment_metrics(spec["area"], spec["category"])
        data[segment] = {
            **rkr,
            "price_reduction_rate": boliga["price_reduction_rate"],
            "avg_reduction_magnitude": boliga["avg_reduction_magnitude"],
            "amort_free_share": interest_only["share"],
            "source_status": "live",
            "provenance": {"boliga": boliga, "rkr": rkr["rkr_observations"], "ul30": interest_only["observations"]},
        }
    return data


def main():
    print("Fetching live RKR and Boliga market inputs (no fallback data is permitted)...")
    data = fetch_market_data()
    out_path = os.path.join(PROJECT_ROOT, "config", "market_data.json")
    with open(out_path, "w") as handle:
        json.dump(data, handle, indent=2)
    print(f"Live market data written to {out_path}")


if __name__ == "__main__":
    main()
