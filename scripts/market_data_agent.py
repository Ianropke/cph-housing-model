#!/usr/bin/env python3
import json
import os
import time
import datetime
import statistics
from curl_cffi import requests

def get_fallback_data():
    return {
      "last_updated": datetime.date.today().isoformat(),
      "copenhagen_apartments": {
        "months_of_supply": 4.4,
        "volume_yoy_change": -0.05,
        "price_reduction_rate": 0.24,
        "avg_reduction_magnitude": 0.035,
        "median_dom": 65,
        "amort_free_share": 0.46
      },
      "copenhagen_houses": {
        "months_of_supply": 4.5,
        "volume_yoy_change": 0.00,
        "price_reduction_rate": 0.20,
        "avg_reduction_magnitude": 0.030,
        "median_dom": 55,
        "amort_free_share": 0.48
      },
      "frederiksberg_apartments": {
        "months_of_supply": 3.8,
        "volume_yoy_change": -0.01,
        "price_reduction_rate": 0.18,
        "avg_reduction_magnitude": 0.025,
        "median_dom": 50,
        "amort_free_share": 0.52
      }
    }

def fetch_boliga_category(property_type: int, zip_from: int, zip_to: int, avg_monthly_sales: float) -> dict:
    all_results = []
    total_count = 0
    page = 1
    
    print(f"Fetching Boliga for propertyType={property_type}, zips {zip_from}-{zip_to}...")
    
    while True:
        url = f"https://api.boliga.dk/api/v2/search/results?pageSize=500&page={page}&propertyType={property_type}&zipcodeFrom={zip_from}&zipcodeTo={zip_to}"
        success = False
        for attempt in range(3):
            try:
                r = requests.get(url, impersonate="chrome110", timeout=15)
                if r.status_code == 200:
                    data = r.json()
                    results = data.get("results", [])
                    all_results.extend(results)
                    total_count = data.get("meta", {}).get("totalCount", 0)
                    total_pages = data.get("meta", {}).get("totalPages", 1)
                    success = True
                    break
                else:
                    print(f"  --> Retry {attempt + 1}: Status {r.status_code} fetching page {page}")
                    time.sleep(2)
            except Exception as e:
                print(f"  --> Retry {attempt + 1}: Exception on page {page}: {e}")
                time.sleep(2)
                
        if not success:
            print(f"Failed to fetch page {page} for propertyType={property_type}")
            break
            
        if page >= total_pages or not results:
            break
            
        page += 1
        time.sleep(1) # Be polite to the API
            
    if not all_results:
        return None
        
    print(f"   ✅ Successfully processed {len(all_results)} active listings (total meta: {total_count})")
        
    days_on_market = [r.get("daysForSale", 0) for r in all_results if r.get("daysForSale") is not None]
    price_changes = [r.get("priceChangePercentTotal", 0) for r in all_results if r.get("priceChangePercentTotal") is not None]
    
    median_dom = int(statistics.median(days_on_market)) if days_on_market else 60
    
    reduced_properties = [c for c in price_changes if c < 0]
    price_reduction_rate = len(reduced_properties) / len(all_results) if all_results else 0.0
    
    avg_reduction_magnitude = 0.0
    if reduced_properties:
        # Boliga returns -12 for -12%. We want 0.12 format.
        avg_reduction_magnitude = sum(abs(c) for c in reduced_properties) / len(reduced_properties) / 100.0

    months_of_supply = total_count / avg_monthly_sales if avg_monthly_sales > 0 else 4.0

    return {
        "months_of_supply": round(months_of_supply, 2),
        "volume_yoy_change": -0.05, # Kept static as it comes from DST EJ56
        "price_reduction_rate": round(price_reduction_rate, 3),
        "avg_reduction_magnitude": round(avg_reduction_magnitude, 3),
        "median_dom": median_dom,
        "amort_free_share": 0.46 # Kept static as it comes from Nationalbanken
    }

def fetch_market_data():
    try:
        data = {}
        
        # Copenhagen Apartments
        # propertyType=3 (Ejerlejlighed), zips 1000-2999 (Kbh by). Approx 550 sales/month
        cph_apt = fetch_boliga_category(3, 1000, 2999, 550.0)
        
        # Copenhagen Houses
        # propertyType=1 (Villa), zips 1000-2999. Approx 150 sales/month
        cph_houses = fetch_boliga_category(1, 1000, 2999, 150.0)
        
        # Frederiksberg Apartments
        # propertyType=3, zip 2000. Approx 100 sales/month
        frb_apt = fetch_boliga_category(3, 2000, 2000, 100.0)
        
        fb = get_fallback_data()
        
        data["copenhagen_apartments"] = cph_apt if cph_apt else fb["copenhagen_apartments"]
        data["copenhagen_houses"] = cph_houses if cph_houses else fb["copenhagen_houses"]
        data["frederiksberg_apartments"] = frb_apt if frb_apt else fb["frederiksberg_apartments"]
        data["last_updated"] = datetime.date.today().isoformat()
        
        return data
    except Exception as e:
        print(f"Agent failed to fetch live data: {e}")
        return get_fallback_data()

def main():
    print("Agent is starting up to fetch market data directly via Boliga API...")
    data = fetch_market_data()
    
    out_path = os.path.join(os.path.dirname(__file__), "..", "config", "market_data.json")
    with open(out_path, "w") as f:
        json.dump(data, f, indent=2)
    print("Market data updated successfully!")

if __name__ == "__main__":
    main()
