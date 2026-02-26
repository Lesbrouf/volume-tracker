import yfinance as yf
import pandas as pd
import requests
import time
import logging
import json
import os
import sys
import threading
import concurrent.futures

# Setup basic logging to file and stdout
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logging.getLogger('yfinance').setLevel(logging.CRITICAL)

STATUS_FILE = "scan_status.json"
TEMP_FILE = "scan_status.tmp"
DEBUG_FILE = "worker_debug.txt"
status_lock = threading.Lock()
debug_lock = threading.Lock()

def debug_log(msg):
    try:
        with debug_lock:
            with open(DEBUG_FILE, "a", encoding="utf-8") as f:
                f.write(f"{time.strftime('%H:%M:%S')} - {msg}\n")
    except:
        pass

# Clear debug log on start
with open(DEBUG_FILE, "w") as f:
    f.write(f"Scan Started at {time.strftime('%H:%M:%S')}\n")

def update_status(status_data):
    """Writes status atomically-ish by writing to temp and renaming, with RETRY logic for Windows."""
    try:
        with status_lock:
            # Write to temp file first
            with open(TEMP_FILE, 'w') as f:
                json.dump(status_data, f)
                f.flush()
            
            # Atomic swap with RETRIES
            max_retries = 10
            for i in range(max_retries):
                try:
                    if os.path.exists(STATUS_FILE):
                        os.replace(TEMP_FILE, STATUS_FILE)
                    else:
                        os.rename(TEMP_FILE, STATUS_FILE)
                    break 
                except PermissionError:
                    if i < max_retries - 1:
                        time.sleep(0.05) 
                    else:
                        pass # print(f"Failed to update status after {max_retries} retries: Locked.")
                except Exception as e:
                    print(f"Error during replace: {e}")
                    break
    except Exception as e:
        print(f"Error writing status: {e}")

def get_us_tickers():
    CACHE_FILE = "backend_cache/us_tickers.json"
    if not os.path.exists("backend_cache"):
        os.makedirs("backend_cache")
        
    # Check cache
    if os.path.exists(CACHE_FILE):
        try:
            import time
            if time.time() - os.path.getmtime(CACHE_FILE) < 86400:
                with open(CACHE_FILE, 'r') as f:
                    return json.load(f)
        except:
            pass

    try:
        url = "https://raw.githubusercontent.com/rreichel3/US-Stock-Symbols/main/all/all_tickers.txt"
        response = requests.get(url, timeout=10)
        if response.status_code != 200: raise Exception 
        clean_tickers = [t for t in response.text.splitlines() if len(t) < 5 and t.isalpha()]
        
        # Save cache
        with open(CACHE_FILE, 'w') as f:
            json.dump(clean_tickers, f)
            
        return clean_tickers
    except:
        return ['AAPL', 'TSLA', 'AMD', 'NVDA', 'INTC', 'MRNA', 'UNG', 'ADBE']

def get_canadian_tickers():
    try:
        # caching to avoid slow scraping every time
        CACHE_FILE = "tsx_tickers_cache.json"
        
        # Check cache validity (24 hours)
        if os.path.exists(CACHE_FILE):
             import time
             file_age = time.time() - os.path.getmtime(CACHE_FILE)
             if file_age < 86400: # 24 hours
                 with open(CACHE_FILE, 'r') as f:
                     cached = json.load(f)
                     if cached:
                         debug_log(f"Loaded {len(cached)} TSX tickers from cache.")
                         return cached

        # Import dynamically or at top. dealing with it here keeps it contained.
        import tsxList
        debug_log("Scraping TSX tickers using tsxList.py...")
        tickers = tsxList.get_clean_tsx_list()
        
        if tickers:
            with open(CACHE_FILE, 'w') as f:
                json.dump(tickers, f)
            debug_log(f"Scraped and cached {len(tickers)} TSX tickers.")
            return tickers
            
        return [] # Fallback if empty
        
    except Exception as e:
        debug_log(f"Error getting TSX list: {e}")
        # Fallback to a small hardcoded list or empty if script fails
        return ['SHOP.TO', 'RY.TO', 'TD.TO', 'CNR.TO', 'CP.TO']

def process_ticker(ticker, market, config):
    try:
        # PURE BLOCKING DOWNLOAD (Safe in ThreadPool)
        df = yf.download(ticker, period="3y", interval="1wk", progress=False, threads=False)
        
        if df.empty or len(df) < 60: 
            return None
        
        if isinstance(df.columns, pd.MultiIndex):
            try:
                df = df.xs(ticker, level=1, axis=1)
            except:
                debug_log(f"{ticker}: MultiIndex fail")
                return None

        first_date = df.index[0]
        last_date = df.index[-1]
        age_days = (last_date - first_date).days
        if age_days < 700: 
            return None

        df['Close'] = df['Close'].ffill()
        df['Volume'] = df['Volume'].fillna(0)
        
        if df['Volume'].iloc[-12:].median() < 50000: 
            return None

        current_price = df['Close'].iloc[-1]
        two_year_high = df['Close'].iloc[-104:].max()
        
        if two_year_high == 0: return None
        drop_pct = (current_price - two_year_high) / two_year_high * 100
        
        drop_cutoff = config.get('drop_cutoff', -50.0)
        
        if drop_pct > drop_cutoff or drop_pct < -99: 
            return None

        recent_12w = df['Volume'].iloc[-12:]
        baseline_median = df['Volume'].iloc[-64:-12].median()
        if baseline_median == 0: baseline_median = 1
        
        spike_ratio = recent_12w.median() / baseline_median
        active_weeks = sum(v > (baseline_median * 1.3) for v in recent_12w)
        
        vol_L52 = df['Volume'].iloc[-52:].median()
        vol_P52 = df['Volume'].iloc[-104:-52].median()
        if vol_P52 == 0: vol_P52 = 1
        regime_ratio = vol_L52 / vol_P52
        
        match_type = ""
        recent_trend = (current_price - df['Close'].iloc[-12]) / df['Close'].iloc[-12] * 100
        max_ratio = max(spike_ratio, regime_ratio)

        vol_cutoff = config.get('vol_cutoff', 1.8)
        
        if max_ratio < vol_cutoff: 
            return None

        if spike_ratio >= vol_cutoff and active_weeks >= 4 and recent_trend > -10:
            match_type = "🔥 FRESH SPIKE"
        elif regime_ratio >= vol_cutoff and recent_trend > -20:
            match_type = "🏗️ BASE BUILDING"

        if match_type:
            # Fundamentals
            t = yf.Ticker(ticker)
            mkt_cap_usd = 0
            insider_pct = 0
            
            # 1. Market Cap (Fast Info)
            try:
                # Use fast_info for robust market cap
                mkt_cap = t.fast_info.market_cap
                # Also try currency
                currency = t.fast_info.currency
                
                if mkt_cap:
                    if currency == 'CAD': mkt_cap_usd = mkt_cap * 0.70
                    else: mkt_cap_usd = mkt_cap
            except Exception as e:
                debug_log(f"{ticker}: FastInfo Cap Fail: {e}")
                
            # 2. Insider Ownership (Slower, .info)
            try:
                info = t.info 
                insider_pct = info.get('heldPercentInsiders', 0)
                if insider_pct is None: insider_pct = 0
            except Exception as e:
                debug_log(f"{ticker}: Insider Info Fail: {e} (Using 0%)")
                insider_pct = 0

            # FILTERS
            cap_cutoff = config.get('cap_cutoff', 1_000_000_000)
            if mkt_cap_usd < cap_cutoff: 
                debug_log(f"{ticker} ({match_type}): Cap {mkt_cap_usd:,.0f} < {cap_cutoff:,.0f}")
                return None
            
            max_insider = config.get('max_insider', 0.50)
            if insider_pct > max_insider: 
                debug_log(f"{ticker} ({match_type}): Insider {insider_pct:.2f} > {max_insider}")
                return None
            
            if mkt_cap_usd > 1_000_000_000:
                cap_str = f"${mkt_cap_usd/1_000_000_000:.1f}B"
            else:
                cap_str = f"${mkt_cap_usd/1_000_000:.0f}M"
            
            debug_log(f"{ticker}: MATCH CONFIRMED!")
            return {
                "pattern": match_type,
                "ticker": ticker,
                "volume_ratio": round(max_ratio, 2),
                "drop_pct": round(drop_pct, 1),
                "market_cap": cap_str,
                "insider_own": f"{insider_pct*100:.1f}%",
                "market_cap_raw": mkt_cap_usd,
                "insider_own_raw": insider_pct,
                "market": market,
                "checked": False
            }
        return None
    except Exception as e:
        debug_log(f"{ticker}: EXCEPTION {e}")
        return None

if __name__ == "__main__":
    try:
        with open("scan_config.json", "r") as f:
            config = json.load(f)
    except:
        config = {'vol_cutoff': 1.8, 'cap_cutoff': 1000000000, 'max_insider': 0.5}

    import global_tickers

    # Build market map first, then create status
    completed = 0
    market_map = {}
    all_tickers_flat = []

    if config.get('use_us_market', True):
        debug_log("Fetching US tickers...")
        us = get_us_tickers()
        all_tickers_flat.extend(us)
        for t in us: market_map[t] = "US"

    if config.get('use_ca_market', False):
        debug_log("Fetching Canadian tickers...")
        ca = get_canadian_tickers()
        all_tickers_flat.extend(ca)
        for t in ca: market_map[t] = "Canada"

    if config.get('use_euronext', False):
        debug_log("Fetching Euronext tickers...")
        eu = global_tickers.get_cached_or_fetch('euronext', global_tickers.fetch_euronext)
        all_tickers_flat.extend(eu)
        for t in eu: market_map[t] = "Euronext"

    if config.get('use_jpx', False):
        debug_log("Fetching Japan (JPX) tickers...")
        jp = global_tickers.get_cached_or_fetch('jpx', global_tickers.fetch_jpx)
        all_tickers_flat.extend(jp)
        for t in jp: market_map[t] = "Japan"

    if config.get('use_lse', False):
        debug_log("Fetching London (LSE) tickers...")
        gb = global_tickers.get_cached_or_fetch('lse', global_tickers.fetch_lse_wiki)
        all_tickers_flat.extend(gb)
        for t in gb: market_map[t] = "London"

    if config.get('use_hkex', False):
        debug_log("Fetching Hong Kong (HKEX) tickers...")
        hk = global_tickers.get_cached_or_fetch('hkex', global_tickers.fetch_hkex_wiki)
        all_tickers_flat.extend(hk)
        for t in hk: market_map[t] = "Hong Kong"

    if config.get('use_china', False):
        debug_log("Fetching China (SSE/SZSE) tickers...")
        cn = global_tickers.get_cached_or_fetch('china', global_tickers.fetch_china_mojing)
        all_tickers_flat.extend(cn)
        for t in cn: market_map[t] = "China"

    if config.get('use_krx', False):
        debug_log("Fetching Korea (KRX) tickers...")
        kr = global_tickers.get_cached_or_fetch('krx', global_tickers.fetch_korea_finance_data)
        all_tickers_flat.extend(kr)
        for t in kr: market_map[t] = "Korea"

    if config.get('custom_tickers', []):
        ct = [t.strip().upper() for t in config.get('custom_tickers', []) if t.strip()]
        all_tickers_flat.extend(ct)
        for t in ct: market_map[t] = "Custom"

    # Unique and sorted list
    tickers = sorted(list(set(all_tickers_flat)))

    status = {
        "is_running": True,
        "progress": 0,
        "total_tickers": len(tickers),
        "scanned_count": 0,
        "logs": [],
        "results": []
    }
    update_status(status)
    debug_log(f"Starting Scan for {len(tickers)} tickers. Config: {config}")

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        future_to_ticker = {executor.submit(process_ticker, t, market_map.get(t, "Unknown"), config): t for t in tickers}
        
        for future in concurrent.futures.as_completed(future_to_ticker):
            ticker_name = future_to_ticker[future]
            try:
                result = future.result(timeout=20) 
                
                with status_lock:
                    if result:
                        status["results"].append(result)
                        status["logs"].append({"time": time.strftime("%H:%M:%S"), "message": f"FOUND: {result['ticker']} - {result['pattern']}"})
                    
                    completed += 1
                    status["scanned_count"] = completed
                    status["progress"] = (completed / len(tickers)) * 100
                    
                    if completed % 5 == 0: 
                         status["logs"].append({"time": time.strftime("%H:%M:%S"), "message": f"Processed {completed}/{len(tickers)}..."})
                         if len(status["logs"]) > 50: status["logs"].pop(0)

                update_status(status)

            except Exception as e:
                debug_log(f"{ticker_name}: WORKER ERROR {e}")
                completed += 1 

    status["is_running"] = False
    status["progress"] = 100
    status["logs"].append({"time": time.strftime("%H:%M:%S"), "message": "Scan Complete."})
    update_status(status)
