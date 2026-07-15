import requests
from bs4 import BeautifulSoup

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
res = requests.get('https://www.boligsiden.dk/tilsalg', headers=headers)
print("Status:", res.status_code)
if res.status_code == 200:
    soup = BeautifulSoup(res.text, 'html.parser')
    s = soup.find('script', id='__NEXT_DATA__')
    if s:
        print("Length of NEXT_DATA:", len(s.string))
    else:
        print("No NEXT_DATA")
