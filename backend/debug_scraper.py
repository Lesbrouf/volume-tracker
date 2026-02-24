import pandas as pd
import requests
import io

def debug_lse():
    url = "https://en.wikipedia.org/wiki/FTSE_All-Share_Index"
    print(f"Scraping LSE: {url}")
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=headers)
        tables = pd.read_html(io.StringIO(r.text))
        print(f"Found {len(tables)} tables.")
        for i, df in enumerate(tables):
            print(f"\n--- Table {i} ---")
            print(df.columns)
            print(df.head(2))
            if i > 5: break
    except Exception as e:
        print(f"LSE Error: {e}")

def debug_hkex():
    url = "https://en.wikipedia.org/wiki/List_of_companies_listed_on_the_Hong_Kong_Stock_Exchange"
    print(f"Scraping HKEX: {url}")
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=headers)
        tables = pd.read_html(io.StringIO(r.text))
        print(f"Found {len(tables)} tables.")
        for i, df in enumerate(tables):
            print(f"\n--- Table {i} ---")
            print(df.columns)
            print(df.head(2))
            if i > 5: break
    except Exception as e:
        print(f"HKEX Error: {e}")

if __name__ == "__main__":
    debug_lse()
    debug_hkex()
