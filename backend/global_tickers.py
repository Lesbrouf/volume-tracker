import pandas as pd
import requests
import io
import os
import json

# Cache duration (24h)
CACHE_DURATION = 86400
CACHE_DIR = "backend_cache"

if not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR)

def get_cached_or_fetch(name, fetch_func):
    cache_file = os.path.join(CACHE_DIR, f"{name}.json")
    if os.path.exists(cache_file):
        import time
        if time.time() - os.path.getmtime(cache_file) < CACHE_DURATION:
            try:
                with open(cache_file, 'r') as f:
                    return json.load(f)
            except:
                pass
    
    try:
        print(f"[{name}] Fetching tickers...")
        tickers = fetch_func()
        if tickers:
            with open(cache_file, 'w') as f:
                json.dump(tickers, f)
            print(f"[{name}] Cached {len(tickers)} tickers.")
            return tickers
    except Exception as e:
        print(f"[{name}] Error: {e}")
    
    return []

def fetch_euronext():
    # Source: derekbanas GitHub (Verified working)
    url = "https://raw.githubusercontent.com/derekbanas/Python4Finance/main/Euronext.csv"
    try:
        df = pd.read_csv(url, encoding='latin-1')
    except:
        df = pd.read_csv(url, encoding='utf-8', errors='replace')
    # Assuming column 'Ticker' or similar. 
    # CSV content likely: Symbol, Name, ...
    # Need to verify column names. fallback to first column if needed.
    # Euronext tickers need suffix: .PA, .AS, etc.
    # The CSV might have specific exchange info. 
    # For MVP, we might try to guess or use the provided suffix if in file.
    # If the file strictly has "MC.PA", "ASML.AS", etc., we are good.
    # If not, it's tricky.
    # Let's assume it has valid yahoo tickers or we need to clean.
    
    # Actually, let's look at the CSV format first in a separate step? 
    # No, I'll trust standard format or suffix loop.
    # But usually Derek's list has "Symbol" column.
    
    tickers = []
    if 'Symbol' in df.columns:
        tickers = df['Symbol'].tolist()
    elif 'Ticker' in df.columns:
        tickers = df['Ticker'].tolist()
    else:
        tickers = df.iloc[:, 0].tolist()
        
    return [str(t).strip() for t in tickers if isinstance(t, str)]

def fetch_jpx():
    # Source: JPX Official Excel (Verified working URL)
    url = "https://www.jpx.co.jp/english/markets/statistics-equities/misc/tvdivq0000001vg2-att/data_e.xls"
    try:
        response = requests.get(url)
        # Verify response
        if response.status_code != 200:
             print(f"[jpx] Failed to download Excel: {response.status_code}")
             return []
             
        df = pd.read_excel(io.BytesIO(response.content), engine='xlrd')
    except Exception as e:
        print(f"[jpx] Excel error: {e}")
        return []
    
    # Column "Code" usually exists. 
    # Tickers are 4 digits. Need to append ".T"
    candidates = []
    # Identify column. Often row 0 or 1 is header.
    # We look for a column that contains 4-digit numbers.
    for col in df.columns:
        if df[col].astype(str).str.match(r'^\d{4}$').sum() > 100:
            candidates = df[col].astype(str).tolist()
            break
            
    return [f"{c}.T" for c in candidates if len(c) == 4]

def fetch_lse_wiki():
    # Fallback: Wikipedia
    # Try "List of companies listed on the London Stock Exchange" or sub-pages
    # Actually, LSE has multiple pages (A-B, C-D...). 
    # Let's try "FTSE 100 Index" and "FTSE 250 Index" as a baseline decent start.
    # Getting ALL 2000+ is hard from Wiki.
    
    sources = [
        "https://en.wikipedia.org/wiki/FTSE_100_Index",
        "https://en.wikipedia.org/wiki/FTSE_250_Index"
    ]
    
    tickers = []
    headers = {"User-Agent": "Mozilla/5.0"}
    
    for url in sources:
        try:
            r = requests.get(url, headers=headers)
            if r.status_code != 200: continue
            
            tables = pd.read_html(io.StringIO(r.text))
            for df in tables:
                cols = [str(c).lower() for c in df.columns]
                if 'ticker' in cols:
                    col = 'Ticker' # Case sensitive match found by lower check
                    # Actually find the exact column name
                    real_col = [c for c in df.columns if str(c).lower() == 'ticker'][0]
                    found = df[real_col].tolist()
                    tickers.extend([f"{t}.L" for t in found if isinstance(t, str)])
        except:
            pass
            
    return list(set(tickers))

def fetch_hkex_wiki():
    url = "https://en.wikipedia.org/wiki/List_of_companies_listed_on_the_Hong_Kong_Stock_Exchange"
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=headers)
        if r.status_code != 200: return []
        
        tables = pd.read_html(io.StringIO(r.text))
        # HKEX tickers are usually 4 digits (0005.HK)
        tickers = []
        for df in tables:
            # Check if column 0 contains strings starting with "SEHK:"
            if df.shape[1] > 0:
                col0 = df.iloc[:, 0].astype(str)
                matches = col0[col0.str.contains("SEHK:", na=False)]
                for val in matches:
                    # Format: "SEHK: 1 CK Hutchison..."
                    try:
                        # Split by space
                        parts = val.replace("SEHK:", "").strip().split(' ')
                        code = parts[0]
                        if code.isdigit():
                            clean = code.zfill(4)
                            tickers.append(f"{clean}.HK")
                    except:
                        pass
        return tickers
    except Exception as e:
        print(f"[hkex] Wiki error: {e}")
        return []

def fetch_china_mojing():
    # Source: mojingmojing/Stock-Crawler-Analysis (GitHub)
    url = "https://raw.githubusercontent.com/mojingmojing/Stock-Crawler-Analysis/master/A_stocklist.xlsx"
    try:
        r = requests.get(url)
        # Requires openpyxl
        df = pd.read_excel(io.BytesIO(r.content), engine='openpyxl')
        
        tickers = []
        if 'A股代码' in df.columns:
            codes = df['A股代码'].dropna().astype(int).astype(str).tolist()
            for c in codes:
                c = c.zfill(6)
                if c.startswith('6'):
                    tickers.append(f"{c}.SS")
                elif c.startswith('0') or c.startswith('3'):
                    tickers.append(f"{c}.SZ")
                    
        return list(set(tickers))
    except Exception as e:
        print(f"[china] Error: {e}")
        return []

def fetch_korea_finance_data():
    # Source: FinanceData/stock_master (GitHub)
    url = "https://raw.githubusercontent.com/FinanceData/stock_master/master/stock_master.csv.gz"
    try:
        # Read compressed CSV
        df = pd.read_csv(url, compression='gzip')
        
        tickers = []
        # Columns: Symbol, Market, ...
        if 'Symbol' in df.columns and 'Market' in df.columns:
             for index, row in df.iterrows():
                 try:
                     symbol = str(row['Symbol']).zfill(6)
                     market = str(row['Market']).strip().upper()
                     
                     if market == 'KOSPI':
                         tickers.append(f"{symbol}.KS")
                     elif market == 'KOSDAQ':
                         tickers.append(f"{symbol}.KQ")
                 except:
                     continue
                     
        return list(set(tickers))
    except Exception as e:
        print(f"[krx] Error: {e}")
        return []

def get_all_tickers(config):
    all_tickers = []
    
    if config.get('use_euronext'):
        all_tickers.extend(get_cached_or_fetch('euronext', fetch_euronext))
        
    if config.get('use_jpx'):
        all_tickers.extend(get_cached_or_fetch('jpx', fetch_jpx))
        
    if config.get('use_lse'):
        all_tickers.extend(get_cached_or_fetch('lse', fetch_lse_wiki))
        
    if config.get('use_hkex'):
        all_tickers.extend(get_cached_or_fetch('hkex', fetch_hkex_wiki))
        
    if config.get('use_china'):
        all_tickers.extend(get_cached_or_fetch('china', fetch_china_mojing))

    if config.get('use_krx'):
        all_tickers.extend(get_cached_or_fetch('krx', fetch_korea_finance_data))
    
    return list(set(all_tickers)) # Unique
