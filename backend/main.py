from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import uvicorn
import csv
import io
import json
import subprocess
import os
import signal
import sys
from fastapi.responses import StreamingResponse
try:
    from . import ticker_utils
except ImportError:
    import ticker_utils

app = FastAPI(title="Volume Tracker API")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ScanConfig(BaseModel):
    vol_cutoff: float = 1.8
    cap_cutoff: float = 1_000_000_000
    max_insider: float = 0.50
    drop_cutoff: float = -50.0
    use_us_market: bool = True
    use_ca_market: bool = True
    use_euronext: bool = False
    use_lse: bool = False
    use_hkex: bool = False
    use_china: bool = False
    use_krx: bool = False
    use_jpx: bool = False
    custom_tickers: List[str] = []

class ToggleCheckedRequest(BaseModel):
    ticker: str
    checked: bool

SCAN_PROCESS = None
STATUS_FILE = "scan_status.json"
CONFIG_FILE = "scan_config.json"

# CACHE for Robustness
LAST_KNOWN_STATUS = {
    "progress": 0,
    "is_running": False,
    "total_tickers": 0,
    "scanned_count": 0,
    "logs": [],
    "results": []
}

@app.get("/")
def read_root():
    return {"message": "Volume Tracker API is running"}

@app.get("/api/tickers")
def get_tickers():
    return ticker_utils.get_all_cached_tickers()

@app.post("/api/scan/start")
def start_scan(config: ScanConfig):
    global SCAN_PROCESS, LAST_KNOWN_STATUS
    
    if SCAN_PROCESS and SCAN_PROCESS.poll() is None:
        SCAN_PROCESS.terminate()
        try:
            SCAN_PROCESS.wait(timeout=2)
        except:
            SCAN_PROCESS.kill()
    
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config.dict(), f)
    
    # Reset Cache
    LAST_KNOWN_STATUS = {
        "progress": 0,
        "is_running": True,
        "total_tickers": 0,
        "scanned_count": 0,
        "logs": [{"time": "", "message": "Starting Process..."}],
        "results": []
    }
    
    with open(STATUS_FILE, 'w') as f:
        json.dump(LAST_KNOWN_STATUS, f)

    python_exe = sys.executable
    # Create console-less subprocess on Windows if needed, but for now standard is fine
    SCAN_PROCESS = subprocess.Popen([python_exe, "scanner_worker.py"])
    
    return {"status": "started", "message": "Scan started in background process"}

@app.get("/api/scan/stop")
def stop_scan():
    global SCAN_PROCESS
    if SCAN_PROCESS and SCAN_PROCESS.poll() is None:
        SCAN_PROCESS.terminate()
        return {"status": "stopped", "message": "Stop requested"}
    return {"status": "stopped", "message": "No active scan"}

@app.get("/api/scan/status")
def get_status():
    global SCAN_PROCESS, LAST_KNOWN_STATUS
    
    is_alive = SCAN_PROCESS is not None and SCAN_PROCESS.poll() is None
    
    try:
        if os.path.exists(STATUS_FILE):
            # Try to read
            try:
                with open(STATUS_FILE, 'r') as f:
                    data = json.load(f)
                
                # If we got here, data is valid. Update cached.
                LAST_KNOWN_STATUS = data
                
            except (json.JSONDecodeError, ValueError, IOError):
                # READ FAILED (Empty file or race condition)
                # Ignore this read, return LAST_KNOWN_STATUS
                pass
            
            # Update alive status on the returned object (cache or fresh)
            if not is_alive and LAST_KNOWN_STATUS.get("is_running", False):
                 LAST_KNOWN_STATUS["is_running"] = False
            
            return LAST_KNOWN_STATUS

    except Exception as e:
        # Fallback
        pass
        
    return LAST_KNOWN_STATUS

@app.post("/api/results/toggle-checked")
def toggle_checked(req: ToggleCheckedRequest):
    global LAST_KNOWN_STATUS
    
    # Update in memory
    results = LAST_KNOWN_STATUS.get("results", [])
    found = False
    for r in results:
        if r['ticker'] == req.ticker:
            r['checked'] = req.checked
            found = True
            break
    
    if found:
        # Persist to file
        if os.path.exists(STATUS_FILE):
            try:
                # Use a lock-like pattern by writing to temp and renaming if we were in the worker, 
                # but here we just overwrite for simplicity since it's user interaction.
                # However, to be safe against the worker's atomic writes:
                with open(STATUS_FILE, 'w') as f:
                    json.dump(LAST_KNOWN_STATUS, f)
            except:
                pass
        return {"status": "updated"}
    
    return {"status": "not_found"}

@app.get("/api/export")
def export_results():
    results = []
    # Read from file or cache? File is safer for "Final" export
    if os.path.exists(STATUS_FILE):
        try:
            with open(STATUS_FILE, 'r') as f:
                data = json.load(f)
                results = data.get("results", [])
        except:
            pass
    
    # Fallback to cache if file read fails
    if not results:
        results = LAST_KNOWN_STATUS.get("results", [])

    if not results:
        return {"error": "No results to export"}
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    headers = ["Ticker", "Pattern", "Volume Ratio", "Drop %", "Market Cap", "Insider Own %", "Market", "Checked"]
    writer.writerow(headers)
    
    for r in results:
        writer.writerow([
            r['ticker'],
            r['pattern'],
            r['volume_ratio'],
            r['drop_pct'],
            r['market_cap'],
            r['insider_own'],
            r.get('market', 'Unknown'),
            r.get('checked', False)
        ])
        
    output.seek(0)
    
    response = StreamingResponse(iter([output.getvalue()]), media_type="text/csv")
    response.headers["Content-Disposition"] = "attachment; filename=scan_results.csv"
    return response

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
