import os
import json
import glob

def get_all_cached_tickers():
    """
    Reads all available ticker caches and returns a dict:
    {
        "US": [...],
        "Canada": [...],
        "Euronext": [...],
        ...
    }
    """
    result = {}
    
    # 1. US Tickers (backend_cache/us_tickers.json)
    if os.path.exists("backend_cache/us_tickers.json"):
        with open("backend_cache/us_tickers.json", "r") as f:
            result["US"] = json.load(f)
            
    # 2. Canada (tsx_tickers_cache.json - root dir)
    if os.path.exists("tsx_tickers_cache.json"):
        with open("tsx_tickers_cache.json", "r") as f:
            result["Canada (TSX)"] = json.load(f)
            
    # 3. Global Markets (backend_cache/*.json)
    # Map filenames to readable names
    name_map = {
        "euronext": "Euronext",
        "jpx": "Japan (JPX)",
        "lse": "London (LSE)",
        "hkex": "Hong Kong (HKEX)",
        "china": "China (SSE/SZSE)",
        "krx": "Korea (KRX)"
    }
    
    cache_files = glob.glob("backend_cache/*.json")
    for cf in cache_files:
        basename = os.path.basename(cf).replace(".json", "")
        if basename == "us_tickers": continue # Already handled
        
        display_name = name_map.get(basename, basename.upper())
        try:
            with open(cf, "r") as f:
                result[display_name] = json.load(f)
        except:
            pass
            
    return result
