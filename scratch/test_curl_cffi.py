import re
from curl_cffi import requests

def run():
    print("Fetching Boligsiden with curl_cffi...")
    # Using impersonate='chrome110' is extremely effective at bypassing Cloudflare
    response = requests.get(
        "https://www.boligsiden.dk/tilsalg?municipality=K%C3%B8benhavn&itemType=Ejerlejlighed",
        impersonate="chrome110"
    )
    
    body_text = response.text
    print(f"Response code: {response.status_code}")
    print("--- FIRST 500 CHARS ---")
    print(body_text[:500])
    
    if "Just a moment" in body_text or "Udfører sikkerhedsverificering" in body_text:
        print("Blocked by Cloudflare.")
    else:
        print("Success! Finding results count...")
        # Since this is raw HTML (maybe React), we might need to look for JSON state or text
        match = re.search(r"af ([\d\.]+) (boliger|resultater)", body_text, re.IGNORECASE)
        if match:
            print("FOUND COUNT:", match.group(1))
        else:
            # Let's search for any number close to 'boliger'
            print("Regex didn't match. Searching for 'boliger'")
            for line in body_text.splitlines():
                if 'boliger' in line.lower() and re.search(r'\d', line):
                    print(line[:200])

if __name__ == "__main__":
    run()
