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

    ssl_context = ssl._create_unverified_context()
    api_url = "https://api.statbank.dk/v1/data"
    
    results = {
        "unemployment_rate": 0.042, # Fallback
        "rent_index": 120.0,
        "disposable_income_cph": 390000.0,
        "disposable_income_frb": 440000.0,
    }
    
    def post_req(payload):
        req_data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            api_url,
            data=req_data,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=5.0, context=ssl_context) as res:
            return json.loads(res.read().decode("utf-8"))

    # 1. Unemployment (AUP01 - 101 Kbh by)
    try:
        data = post_req({
            "table": "AUP01",
            "format": "JSONSTAT",
            "variables": [
                {"code": "OMRÅDE", "values": ["101"]},
                {"code": "ALDER", "values": ["TOT"]},
                {"code": "KØN", "values": ["TOT"]},
                {"code": "Tid", "values": ["*"]}
            ]
        })
        val = data["dataset"]["value"][-1]
        if val is not None:
            results["unemployment_rate"] = val / 100.0
    except Exception as e:
        print(f"Warning: Failed to fetch AUP01: {e}")

    # 2. Rent Index (PRIS111 - 041100 Faktisk husleje)
    try:
        data = post_req({
            "table": "PRIS111",
            "format": "JSONSTAT",
            "variables": [
                {"code": "VAREGR", "values": ["041100"]},
                {"code": "ENHED", "values": ["100"]},
                {"code": "Tid", "values": ["*"]}
            ]
        })
        val = data["dataset"]["value"][-1]
        if val is not None:
            results["rent_index"] = val
    except Exception as e:
        print(f"Warning: Failed to fetch PRIS111: {e}")

    # 3. Income (INDKP107 - 105 Disponibel indkomst, 116 Gennemsnit)
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
            val = data["dataset"]["value"][-1]
            if val is not None:
                if omrade == "101":
                    results["disposable_income_cph"] = float(val)
                else:
                    results["disposable_income_frb"] = float(val)
    except Exception as e:
        print(f"Warning: Failed to fetch INDKP107: {e}")
        
    _macro_data_cache = results
    return results
