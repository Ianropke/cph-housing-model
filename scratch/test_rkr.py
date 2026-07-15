import requests

url = "https://rkr.statistikbank.dk/statbank5a/default.asp"
print("Testing rkr.statistikbank.dk...")
try:
    res = requests.get(url, timeout=5)
    print("Status:", res.status_code)
except Exception as e:
    print("Error:", e)
