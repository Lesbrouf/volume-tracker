import subprocess
import time
import os
import signal
import sys
import webbrowser

def run_app():
    print("==============================================")
    print("   Volume Tracker Pro - Launcher")
    print("==============================================")
    
    # Paths
    base_dir = os.path.dirname(os.path.abspath(__file__))
    backend_dir = os.path.join(base_dir, "backend")
    frontend_dir = os.path.join(base_dir, "frontend")
    
    # Log files - OPEN WITH UTF-8
    backend_log = open(os.path.join(base_dir, "backend.log"), "w", encoding="utf-8")
    frontend_log = open(os.path.join(base_dir, "frontend.log"), "w", encoding="utf-8")

    # Environment variables to force UTF-8
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"

    def kill_port(port):
        try:
            # Find PID using netstat
            import subprocess
            result = subprocess.check_output(f"netstat -ano | findstr :{port}", shell=True).decode()
            for line in result.splitlines():
                if "LISTENING" in line:
                    pid = line.strip().split()[-1]
                    if int(pid) > 0:
                        print(f"Cleaning up old process on port {port} (PID: {pid})...")
                        subprocess.call(f"taskkill /F /T /PID {pid}", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            pass

    # Kill old processes to prevent address already in use
    kill_port(8000)
    kill_port(5173)

    print("[1/3] Starting Backend (FastAPI)...")
    # Using python -m uvicorn to ensure we use the same python env
    backend_process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"],
        cwd=backend_dir,
        stdout=backend_log,
        stderr=backend_log,
        env=env # Pass environment
    )
    
    print("[2/3] Starting Frontend (Vite)...")
    # npm needs shell=True on Windows
    frontend_process = subprocess.Popen(
        ["npm", "run", "dev"],
        cwd=frontend_dir,
        shell=True,
        stdout=frontend_log,
        stderr=frontend_log,
        env=env
    )

    print("[3/3] Waiting for services to initialize...")
    time.sleep(3)
    
    print("\n✅ App is running!")
    print("   -> Frontend: http://localhost:5173")
    print("   -> Backend:  http://localhost:8000")
    print("   -> Logs:     backend.log, frontend.log")
    print("\nPress Ctrl+C to stop the application.")
    
    # Open browser automatically
    try:
        webbrowser.open("http://localhost:5173")
    except:
        pass

    try:
        while True:
            time.sleep(1)
            # Check if processes are still alive
            if backend_process.poll() is not None:
                print("❌ Backend process died! Check backend.log")
                break
            # Frontend is shell=True so poll() checks the cmd.exe, not node. 
            
    except KeyboardInterrupt:
        print("\n🛑 Stopping application...")
        
    finally:
        # Cleanup
        print("   Terminating Backend...")
        backend_process.terminate()
        
        print("   Terminating Frontend...")
        subprocess.call(["taskkill", "/F", "/T", "/PID", str(frontend_process.pid)])
        
        backend_log.close()
        frontend_log.close()
        print("   Done. Bye!")

if __name__ == "__main__":
    run_app()
