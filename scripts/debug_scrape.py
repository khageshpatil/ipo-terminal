"""Find subscription/list page with open+close dates for all IPOs."""
import re, json
from curl_cffi import requests as cr
from bs4 import BeautifulSoup

def safe(s): return str(s).encode("ascii","replace").decode("ascii")

urls = [
    "https://www.chittorgarh.com/report/ipo-in-india-list-main-board-sme/82/all/?year=2024",
    "https://www.chittorgarh.com/ipo/ipo_dashboard.asp",
    "https://www.chittorgarh.com/report/ipo-subscription-status/ipo_subscription.asp",
]

for url in urls:
    r = cr.get(url, impersonate="chrome124", timeout=30)
    soup = BeautifulSoup(r.text, "lxml")
    all_text = ""
    for s in soup.find_all("script"):
        txt = s.string or ""
        if "self.__next_f.push" in txt:
            m = re.search(r'self\.__next_f\.push\(\[1,"(.+?)"\]\)', txt, re.DOTALL)
            if m:
                try: inner = json.loads('"' + m.group(1) + '"'); all_text += inner
                except: pass
    
    print(f"\n{url}")
    print(f"Status: {r.status_code}, RSC len: {len(all_text)}")
    
    # Search for date-related keys
    for kw in ['"open_date"', '"close_date"', '"ipo_open_date"', '"ipo_close_date"',
               '"subscription_start_date"', '"ipo_subscription_date"', '"allotment_date"']:
        if kw in all_text:
            idx = all_text.find(kw)
            print(f"  {kw}: ...{safe(all_text[idx:idx+60])}...")

    # Find first JSON array in response
    list_matches = re.finditer(r'"([a-z_]+)":\s*\[(\{[^}]{50,})', all_text[:80000])
    for match in list_matches:
        key = match.group(1)
        sample = safe(match.group(2)[:200])
        if any(d in sample.lower() for d in ['date', 'open', 'close', '2024', '2023']):
            print(f"  Array '{key}': {sample}")
            break
