import requests
import json

headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
    'Accept': 'application/json'
}

print("Testing api.boligsiden.dk...")
try:
    res = requests.get('https://api.boligsiden.dk/search/cases?zipCodes=1000,2000&itemTypes=Ejerlejlighed', headers=headers, timeout=5)
    print("Status:", res.status_code)
except Exception as e:
    print("Error:", e)
