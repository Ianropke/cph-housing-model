"""
Module to fetch real macro economic data from Danmarks Statistik (DST).
"""
import urllib.request
import json
import ssl

# Cache to avoid re-fetching multiple times per segment
_macro_data_cache = None


def fetch_dst_macro_data() -> dict:
    """
    Fetches real macro economic data from Danmarks Statistik (DST)
    to replace simulated EWI data.
    """
    global _macro_data_cache
    if _macro_data_cache is not None:
        return _macro_data_cache

    # Keep normal certificate validation enabled. The data is used in
    # production model calculations and must not be fetched over an
    # unverified TLS connection.
    ssl_context = ssl.create_default_context()
    api_url = "https://api.statbank.dk/v1/data"

    results = {
        "unemployment_rate": 0.042, # Fallback
        "unemployment_period": None,
        "unemployment_updated": None,
        "rent_index": 120.0,
        "rent_period": None,
        "rent_updated": None,
        "rent_series": {},
        "disposable_income_cph": 390000.0,
        "disposable_income_frb": 440000.0,
        "income_period": None,
        "income_updated": None,
        "interest_rate": 0.039, # Fallback
        "interest_period": None,
        "interest_updated": None,
    }

    def post_req(payload):
        req_data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            api_url,
            data=req_data,
            headers={
                "Content-Type": "application/json",
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
            },
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=8.0, context=ssl_context) as res:
            return json.loads(res.read().decode("utf-8"))

    # 1. Unemployment (AUS07 - Sæsonkorrigeret i pct af arbejdsstyrken)
    try:
        data = post_req({
            "table": "AUS07",
            "format": "JSONSTAT",
            "variables": [
                {"code": "YD", "values": ["TOT"]},
                {"code": "SAESONFAK", "values": ["9"]},
                {"code": "Tid", "values": ["*"]}
            ]
        })
        vals = data["dataset"]["value"]
        tid_keys = list(data["dataset"]["dimension"]["Tid"]["category"]["index"].keys())
        updated_str = data["dataset"].get("updated")
        for i in range(len(vals)-1, -1, -1):
            if vals[i] is not None:
                results["unemployment_rate"] = vals[i] / 100.0
                results["unemployment_period"] = tid_keys[i]
                if updated_str:
                    results["unemployment_updated"] = updated_str.split("T")[0]
                break
    except Exception as e:
        print(f"Warning: Failed to fetch AUS07: {e}")

    # 2. Interest Rate (DNRENTM - Nationalbankens Indskudsbevisrente)
    try:
        data = post_req({
            "table": "DNRENTM",
            "format": "JSONSTAT",
            "variables": [
                {"code": "INSTRUMENT", "values": ["OIBNAA"]},
                {"code": "LAND", "values": ["DK"]},
                {"code": "OPGOER", "values": ["E"]},
                {"code": "Tid", "values": ["*"]}
            ]
        })
        vals = data["dataset"]["value"]
        tid_keys = list(data["dataset"]["dimension"]["Tid"]["category"]["index"].keys())
        updated_str = data["dataset"].get("updated")
        for i in range(len(vals)-1, -1, -1):
            if vals[i] is not None:
                results["interest_rate"] = vals[i] / 100.0
                results["interest_period"] = tid_keys[i]
                if updated_str:
                    results["interest_updated"] = updated_str.split("T")[0]
                break
    except Exception as e:
        print(f"Warning: Failed to fetch DNRENTM: {e}")

    # 3. Rent Index (HUS1 - Huslejeindeks for boliger, Region Hovedstaden, Boliger i alt)
    try:
        data = post_req({
            "table": "HUS1",
            "format": "JSONSTAT",
            "variables": [
                {"code": "REGION", "values": ["084"]}, # Region Hovedstaden
                {"code": "EJENDOMSKATE", "values": ["550"]}, # Boliger i alt
                {"code": "TAL", "values": ["100"]}, # Indeks
                {"code": "Tid", "values": ["*"]}
            ]
        })
        vals = data["dataset"]["value"]
        tid_keys = list(data["dataset"]["dimension"]["Tid"]["category"]["index"].keys())
        updated_str = data["dataset"].get("updated")

        rent_series = {}
        for t, val in zip(tid_keys, vals):
            if val is not None:
                q_key = t.replace("K", "Q")
                rent_series[q_key] = val
        results["rent_series"] = rent_series

        for i in range(len(vals)-1, -1, -1):
            if vals[i] is not None:
                results["rent_index"] = vals[i]
                results["rent_period"] = tid_keys[i].replace("K", "Q")
                if updated_str:
                    results["rent_updated"] = updated_str.split("T")[0]
                break
    except Exception as e:
        print(f"Warning: Failed to fetch HUS1: {e}")

    # 4. Income (INDKP107 - 105 Disponibel indkomst, 116 Gennemsnit)
    try:
        for omrade in ["101", "147"]:
            data = post_req({
                "table": "INDKP107",
                "format": "JSONSTAT",
                "variables": [
                    {"code": "OMRÅDE", "values": [omrade]},
                    {"code": "ENHED", "values": ["116"]},
                    {"code": "KOEN", "values": ["MOK"]},
                    {"code": "UDDNIV", "values": ["10"]},
                    {"code": "INDKOMSTTYPE", "values": ["105"]},
                    {"code": "Tid", "values": ["*"]}
                ]
            })
            vals = data["dataset"]["value"]
            tid_keys = list(data["dataset"]["dimension"]["Tid"]["category"]["index"].keys())
            updated_str = data["dataset"].get("updated")
            for i in range(len(vals)-1, -1, -1):
                if vals[i] is not None:
                    if omrade == "101":
                        results["disposable_income_cph"] = float(vals[i])
                    else:
                        results["disposable_income_frb"] = float(vals[i])
                    results["income_period"] = tid_keys[i]
                    if updated_str:
                        results["income_updated"] = updated_str.split("T")[0]
                    break
    except Exception as e:
        print(f"Warning: Failed to fetch INDKP107: {e}")

    _macro_data_cache = results
    return results
