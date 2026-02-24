import pandas as pd
import requests
import io
import sys

# Force UTF-8 for console output
sys.stdout.reconfigure(encoding='utf-8')

def inspect_china():
    url = "https://raw.githubusercontent.com/mojingmojing/Stock-Crawler-Analysis/master/A_stocklist.xlsx"
    print(f"Downloading China list: {url}")
    try:
        r = requests.get(url)
        df = pd.read_excel(io.BytesIO(r.content), engine='openpyxl')
        print("China Columns:", df.columns.tolist())
        # Print A-share code column
        if 'A股代码' in df.columns:
             print("A-Share Codes:", df['A股代码'].iloc[:10].tolist())
        else:
             print("Column 'A股代码' not found.")
    except Exception as e:
        print(f"China Error: {e}")

def inspect_korea():
    url = "https://raw.githubusercontent.com/FinanceData/stock_master/master/stock_master.csv.gz"
    print(f"Downloading Korea list: {url}")
    try:
        df = pd.read_csv(url, compression='gzip')
        print("Korea Columns:", df.columns.tolist())
        print(df.head())
    except Exception as e:
        print(f"Korea Error: {e}")

if __name__ == "__main__":
    inspect_china()
    inspect_korea()
