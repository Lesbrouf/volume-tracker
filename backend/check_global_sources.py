import requests

def check_url(url):
    try:
        r = requests.head(url, timeout=5)
        print(f"[{r.status_code}] {url}")
        return r.status_code == 200
    except Exception as e:
        print(f"[ERR] {url}: {e}")
        return False

urls = [
    # HKEX (Direct)
    "https://www.hkex.com.hk/eng/market/sec_tradinfo/stockcode/ListOfSecurities.xlsx",
    "https://www.hkex.com.hk/eng/market/sec_tradinfo/stockcode/ListOfSecurities.xls",
    
    # China (Stock-Crawler-Analysis)
    "https://raw.githubusercontent.com/mojingmojing/Stock-Crawler-Analysis/master/A_stocklist.xlsx",
    
    
    # Korea (FinanceData - stock_master)
    "https://raw.githubusercontent.com/FinanceData/stock_master/master/stock_master.csv.gz",
    "https://raw.githubusercontent.com/FinanceData/stock_master/master/stock_master.csv",
    # Korea (kshan226)
    "https://raw.githubusercontent.com/kshan226/stock/master/kospi.csv",
    "https://raw.githubusercontent.com/kshan226/stock/master/kosdaq.csv",
    "https://www.jpx.co.jp/english/markets/statistics-equities/misc/tvdivq0000001vg2-att/data_e.xls",
    
    # Euronext (Confirmed working)
    "https://raw.githubusercontent.com/derekbanas/Python4Finance/main/Euronext.csv",
    
    # Korea (GitHub)
    "https://raw.githubusercontent.com/FinanceData/stock_master/master/stock_master.csv", # Failed last time, checking alternative?
    "https://raw.githubusercontent.com/FinanceData/FinanceDataReader/master/krx/krx.csv" # Another guess
]

print("Checking URLs...")
for u in urls:
    check_url(u)
