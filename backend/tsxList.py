import pandas as pd
import requests
import io
import yfinance as yf

def get_clean_tsx_list():
    url = "https://en.wikipedia.org/wiki/S%26P/TSX_Composite_Index"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    # --- STEP 1: SCRAPE WIKIPEDIA ---
    print("1. Scraping Wikipedia for raw list...")
    try:
        response = requests.get(url, headers=headers)
        tables = pd.read_html(io.StringIO(response.text))
        
        target_df = None
        for df in tables:
            cols = [str(c).lower() for c in df.columns]
            if 'symbol' in cols or 'ticker' in cols:
                target_df = df
                ticker_col = 'Symbol' if 'Symbol' in df.columns else 'Ticker'
                break
        
        if target_df is None:
            print("[ERROR] Could not find ticker table.")
            return []

        # Clean formatting (Switch Wikipedia '.' to Yahoo '-')
        raw_tickers = target_df[ticker_col].tolist()
        candidates = []
        for t in raw_tickers:
            t = str(t).split(' ')[0] # Remove footnotes
            t = t.replace('.', '-') + '.TO'
            candidates.append(t)
            
        print(f"   Found {len(candidates)} candidates. Checking for delisted stocks...")

        # --- STEP 2: REMOVE "DEAD" STOCKS (The crucial step) ---
        # We download 1 day of data for ALL stocks at once. 
        # yfinance automatically ignores the dead ones and tells us which failed.
        
        data = yf.download(candidates, period="1d", progress=False)['Close']
        
        # 'data' will only contain columns for stocks that actually returned data.
        # If CIX.TO is dead, it simply won't be a column in this dataframe.
        
        if isinstance(data, pd.DataFrame):
            # Get list of columns that are NOT empty
            valid_tickers = data.columns[data.notna().any()].tolist()
        else:
            # If only 1 stock was valid, data is a Series, not DataFrame
            valid_tickers = candidates if not data.empty else []

        # Calculate what we removed
        removed = set(candidates) - set(valid_tickers)
        if removed:
            print(f"\n[REMOVED] {len(removed)} DEAD/DELISTED STOCKS:")
            print(f"   {', '.join(list(removed)[:10])} ...") # Show first 10
        
        print(f"\n[SUCCESS] FINAL LIST: {len(valid_tickers)} Active Stocks")
        return sorted(valid_tickers)

    except Exception as e:
        print(f"Error: {e}")
        return []

if __name__ == "__main__":
    final_list = get_clean_tsx_list()
    print("\n# Copy this list:")
    print(final_list)