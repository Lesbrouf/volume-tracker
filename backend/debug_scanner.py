import yfinance as yf
import pandas as pd

tickers = ['AAPL', 'TSLA', 'MSFT', 'NONEXISTENTTICKER']
print(f"Downloading {tickers}...")

try:
    data = yf.download(tickers, period="3y", interval="1wk", progress=False, group_by='ticker', threads=True)
    print("\n--- Data Columns ---")
    print(data.columns)
    
    print("\n--- AAPL Data Head ---")
    if 'AAPL' in data.columns.levels[0]:
        print(data['AAPL'].head())
    else:
        print("AAPL not found in columns")

    print("\n--- Access Test ---")
    for t in tickers:
        try:
            if t in data.columns.levels[0]:
                df = data[t]
                print(f"{t}: Rows={len(df)}")
            else:
                print(f"{t}: Not in columns")
        except Exception as e:
            print(f"{t}: Error {e}")

except Exception as e:
    print(f"Main Error: {e}")
