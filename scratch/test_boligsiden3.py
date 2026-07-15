import requests
from bs4 import BeautifulSoup

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}
res = requests.get('https://www.boligsiden.dk/markedsindeks/udbud', headers=headers)
print("Status:", res.status_code)
soup = BeautifulSoup(res.text, 'html.parser')
for table in soup.find_all('table'):
    print(table.text[:100])
