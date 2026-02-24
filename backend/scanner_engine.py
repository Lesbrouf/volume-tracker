import yfinance as yf
import pandas as pd
import requests
import time
import logging
import threading
import uuid
import traceback

# Setup basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
# Suppress yfinance internal errors
logging.getLogger('yfinance').setLevel(logging.CRITICAL)

logger = logging.getLogger(__name__)

class StockScanner:
    def __init__(self):
        self.stop_requested = False
        self.results = []
        self.logs = []
        self.progress = 0
        self.total_tickers = 0
        self.scanned_count = 0
        self.current_scan_id = None
        self.is_running_flag = False
        self.lock = threading.Lock()
        
    def log(self, message):
        """Adds a log message to the internal log list and prints it."""
        print(message, flush=True) 
        with self.lock:
            self.logs.append({"time": time.strftime("%H:%M:%S"), "message": message})
            if len(self.logs) > 1000:
                self.logs.pop(0)

    @property
    def is_running(self):
        return self.is_running_flag

    def get_us_tickers(self):
        self.log("🌎 Downloading US Ticker List...")
        try:
            url = "https://raw.githubusercontent.com/rreichel3/US-Stock-Symbols/main/all/all_tickers.txt"
            response = requests.get(url, timeout=10)
            if response.status_code != 200:
                raise Exception(f"Failed to download: {response.status_code}")
            clean_tickers = [t for t in response.text.splitlines() if len(t) < 5 and t.isalpha()]
            return clean_tickers
        except Exception as e:
            self.log(f"⚠️ Error fetching US tickers: {e}. Using backup list.")
            return ['AAPL', 'TSLA', 'AMD', 'NVDA', 'INTC', 'MRNA', 'UNG', 'ADBE']

    def get_canadian_tickers(self):
        return ['AAV.TO', 'ABX.TO', 'AC.TO', 'ACO-X.TO', 'AEM.TO', 'AG.TO', 'AGI.TO', 'AIF.TO', 'ALA.TO', 
                'AP-UN.TO', 'AQN.TO', 'ARX.TO', 'ASTL.TO', 'ATD.TO', 'ATH.TO', 'ATRL.TO', 'ATS.TO', 'ATZ.TO', 
                'AYA.TO', 'BAM.TO', 'BB.TO', 'BBD-B.TO', 'BBU-UN.TO', 'BCE.TO', 'BDGI.TO', 'BDT.TO', 'BEI-UN.TO', 
                'BEP-UN.TO', 'BHC.TO', 'BIP-UN.TO', 'BIR.TO', 'BLX.TO', 'BMO.TO', 'BN.TO', 'BNS.TO', 'BTE.TO', 
                'BTO.TO', 'BYD.TO', 'CAE.TO', 'CAR-UN.TO', 'CCA.TO', 'CCL-B.TO', 'CCO.TO', 'CEU.TO', 'CG.TO', 
                'CHP-UN.TO', 'CIGI.TO', 'CJT.TO', 'CLS.TO', 'CM.TO', 'CNQ.TO', 'CNR.TO', 'CP.TO', 'CPX.TO', 
                'CRR-UN.TO', 'CRT-UN.TO', 'CS.TO', 'CSH-UN.TO', 'CSU.TO', 'CTC-A.TO', 'CU.TO', 'CVE.TO', 
                'DFY.TO', 'DIR-UN.TO', 'DML.TO', 'DOL.TO', 'DOO.TO', 'DPM.TO', 'DSG.TO', 'EFN.TO', 'EFR.TO', 
                'EIF.TO', 'ELD.TO', 'EMA.TO', 'EMP-A.TO', 'ENB.TO', 'ENGH.TO', 'EQB.TO', 'EQX.TO', 'ERO.TO', 
                'FCR-UN.TO', 'FFH.TO', 'FM.TO', 'FNV.TO', 'FRU.TO', 'FSV.TO', 'FTS.TO', 'FTT.TO', 'FVI.TO', 
                'GEI.TO', 'GFL.TO', 'GIB-A.TO', 'GIL.TO', 'GRT-UN.TO', 'GSY.TO', 'GWO.TO', 'H.TO', 'HBM.TO', 
                'HR-UN.TO', 'HWX.TO', 'IAG.TO', 'IFC.TO', 'IFP.TO', 'IGM.TO', 'IIP-UN.TO', 'IMG.TO', 'IMO.TO', 
                'IPCO.TO', 'IVN.TO', 'JWEL.TO', 'K.TO', 'KEL.TO', 'KEY.TO', 'KMP-UN.TO', 'KNT.TO', 'KXS.TO', 
                'L.TO', 'LB.TO', 'LIF.TO', 'LNR.TO', 'LSPD.TO', 'LUG.TO', 'LUN.TO', 'MATR.TO', 'MDA.TO', 
                'MFC.TO', 'MFI.TO', 'MG.TO', 'MRU.TO', 'MTL.TO', 'MTY.TO', 'MX.TO', 'NFI.TO', 'NG.TO', 
                'NGD.TO', 'NPI.TO', 'NTR.TO', 'NVA.TO', 'NWC.TO', 'NWH-UN.TO', 'NXE.TO', 'OGC.TO', 'OLA.TO', 
                'ONEX.TO', 'OR.TO', 'OTEX.TO', 'PAAS.TO', 'PBH.TO', 'PD.TO', 'PET.TO', 'PEY.TO', 'PMZ-UN.TO', 
                'POU.TO', 'POW.TO', 'PPL.TO', 'PSI.TO', 'PSK.TO', 'PXT.TO', 'QBR-B.TO', 'QSR.TO', 'RCH.TO', 
                'RCI-B.TO', 'REI-UN.TO', 'RUS.TO', 'RY.TO', 'SAP.TO', 'SEA.TO', 'SES.TO', 'SHOP.TO', 'SIA.TO', 
                'SII.TO', 'SJ.TO', 'SLF.TO', 'SOBO.TO', 'SPB.TO', 'SRU-UN.TO', 'SSRM.TO', 'STN.TO', 'SU.TO', 
                'SVI.TO', 'T.TO', 'TA.TO', 'TCL-A.TO', 'TD.TO', 'TECK-B.TO', 'TFII.TO', 'TFPM.TO', 'TIH.TO', 
                'TLRY.TO', 'TOU.TO', 'TOY.TO', 'TPZ.TO', 'TRI.TO', 'TRP.TO', 'TSU.TO', 'TVE.TO', 'TXG.TO', 
                'VET.TO', 'WCN.TO', 'WCP.TO', 'WDO.TO', 'WFG.TO', 'WN.TO', 'WPK.TO', 'WPM.TO', 'WSP.TO', 'X.TO']

    def process_ticker(self, ticker, config):
        try:
            # 1. DOWNLOAD (Singular, Blocking)
            # threads=False prevents Any nested threading handling
            df = yf.download(ticker, period="3y", interval="1wk", progress=False, threads=False)
            
            if df.empty or len(df) < 60: return None
            
            if isinstance(df.columns, pd.MultiIndex):
                try:
                    df = df.xs(ticker, level=1, axis=1)
                except:
                    return None

            first_date = df.index[0]
            last_date = df.index[-1]
            age_days = (last_date - first_date).days
            if age_days < 700: return None

            df['Close'] = df['Close'].ffill()
            df['Volume'] = df['Volume'].fillna(0)
            
            if df['Volume'].iloc[-12:].median() < 50000: return None

            current_price = df['Close'].iloc[-1]
            two_year_high = df['Close'].iloc[-104:].max()
            
            if two_year_high == 0: return None
            drop_pct = (current_price - two_year_high) / two_year_high * 100
            
            if drop_pct > -50 or drop_pct < -90: return None

            recent_12w = df['Volume'].iloc[-12:]
            baseline_median = df['Volume'].iloc[-64:-12].median()
            if baseline_median == 0: baseline_median = 1
            
            spike_ratio = recent_12w.median() / baseline_median
            active_weeks = sum(v > (baseline_median * 1.3) for v in recent_12w)
            
            # vol_L52 = df['Volume'].iloc[-52:].median()
            # vol_P52 = df['Volume'].iloc[-104:-52].median()
            # if vol_P52 == 0: vol_P52 = 1
            # regime_ratio = vol_L52 / vol_P52
            
            # Reverting calculation to pure basics to avoid index errors
            regime_ratio = 0 
            
            match_type = ""
            recent_trend = (current_price - df['Close'].iloc[-12]) / df['Close'].iloc[-12] * 100
            max_ratio = max(spike_ratio, regime_ratio)

            vol_cutoff = config.get('vol_cutoff', 1.8)
            
            if max_ratio < vol_cutoff: return None

            if spike_ratio >= vol_cutoff and active_weeks >= 4 and recent_trend > -10:
                match_type = "🔥 FRESH SPIKE"
            elif regime_ratio >= vol_cutoff and recent_trend > -20:
                match_type = "🏗️ BASE BUILDING"

            if match_type:
                # FUNDAMENTALS (BLOCKING / RAW)
                try:
                    t = yf.Ticker(ticker)
                    info = t.info # Blocking call
                    
                    mkt_cap = info.get('marketCap', 0)
                    currency = info.get('currency', 'USD')
                    
                    if currency == 'CAD':
                         mkt_cap_usd = mkt_cap * 0.70
                    else:
                         mkt_cap_usd = mkt_cap
                         
                    insider_pct = info.get('heldPercentInsiders', 0)
                    if insider_pct is None: insider_pct = 0
                except:
                    mkt_cap_usd = 0
                    insider_pct = 0

                cap_cutoff = config.get('cap_cutoff', 1_000_000_000)
                if mkt_cap_usd < cap_cutoff: return None
                
                max_insider = config.get('max_insider', 0.50)
                if insider_pct > max_insider: return None
                
                if mkt_cap_usd > 1_000_000_000:
                    cap_str = f"${mkt_cap_usd/1_000_000_000:.1f}B"
                else:
                    cap_str = f"${mkt_cap_usd/1_000_000:.0f}M"
                
                return {
                    "pattern": match_type,
                    "ticker": ticker,
                    "volume_ratio": round(max_ratio, 2),
                    "drop_pct": round(drop_pct, 1),
                    "market_cap": cap_str,
                    "insider_own": f"{insider_pct*100:.1f}%",
                    "market_cap_raw": mkt_cap_usd,
                    "insider_own_raw": insider_pct
                }
            return None
        except Exception as e:
            return None

    def start_scan(self, config):
        new_scan_id = str(uuid.uuid4())
        self.current_scan_id = new_scan_id
        self.stop_requested = False
        self.is_running_flag = True
        
        self.results = []
        self.logs = []
        self.scanned_count = 0
        
        tickers = []
        if config.get('use_us_market', True):
            tickers.extend(self.get_us_tickers())
        if config.get('use_ca_market', True):
             tickers.extend(self.get_canadian_tickers())
        if config.get('custom_tickers', []):
           clean_custom = [t.strip().upper() for t in config.get('custom_tickers', []) if t.strip()]
           tickers.extend(clean_custom)

        tickers = sorted(list(set(tickers)))
        self.total_tickers = len(tickers)
        
        if self.current_scan_id != new_scan_id: return

        self.log(f"📋 Starting scan for {self.total_tickers} tickers (Sequential Mode)...")
        self.log(f"⚙️ Config: Vol > {config.get('vol_cutoff')}, Cap > {config.get('cap_cutoff')}")

        for i, ticker in enumerate(tickers):
            if self.stop_requested or self.current_scan_id != new_scan_id:
                self.log("🛑 Scan stopped.")
                break

            self.log(f"🔍 Checking {i+1}/{len(tickers)}: {ticker}")
            
            try:
                result = self.process_ticker(ticker, config)
                
                if result:
                    with self.lock:
                        self.results.append(result)
                        self.log(f"FOUND: {result['ticker']} - {result['pattern']}") 
                
                # Tiny sleep to ensure the CPU yields and logging flushes
                time.sleep(0.05)
                        
            except Exception as e:
                self.log(f"⚠️ Error loop: {e}")
            
            self.scanned_count += 1
            self.progress = (self.scanned_count / self.total_tickers) * 100

        if self.current_scan_id == new_scan_id:
            if not self.stop_requested:
                self.log("✅ Scan complete.")
                self.progress = 100
            else:
                self.log("🛑 Scan stopped by user.")
            self.is_running_flag = False

    def stop_scan(self):
        self.stop_requested = True
        self.log("🛑 Stop command received.")

scanner = StockScanner()
