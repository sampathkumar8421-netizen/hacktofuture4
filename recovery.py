import os
import subprocess
import time
from pyngrok import ngrok, conf

def recover():
    print("Starting Recovery...")
    
    # 1. Kill stale processes
    # We use a try-except because some might already be dead
    try:
        subprocess.run("taskkill /F /IM uvicorn.exe /T", shell=True, capture_output=True)
    except: pass
    try:
        subprocess.run("taskkill /F /IM ngrok.exe /T", shell=True, capture_output=True)
    except: pass
    
    time.sleep(5)
    
    # 2. Setup Anonymous Ngrok
    # Explicitly clear any token to avoid vanity URL deadlock
    conf.get_default().auth_token = None
    if "NGROK_AUTHTOKEN" in os.environ:
        del os.environ["NGROK_AUTHTOKEN"]
        
    print("Connecting to Ngrok (Anonymous)...")
    try:
        url = ngrok.connect(8000).public_url
        print(f"SUCCESS: {url}")
        with open("recovery_log.txt", "w") as f:
            f.write(f"SUCCESS_URL: {url}\n")
    except Exception as e:
        print(f"FAILED: {e}")
        with open("recovery_log.txt", "w") as f:
            f.write(f"FAILED: {e}\n")
        return

    # 3. Start Backend
    print("Starting Backend...")
    env = os.environ.copy()
    env["PYTHONPATH"] = r"C:\Users\ASUS\Downloads\argoland"
    # Use Popen to keep it running in background
    subprocess.Popen(["uvicorn", "lily02_backend.main:app", "--host", "0.0.0.0", "--port", "8000"], env=env)
    
    print("Workstation Restored.")
    while True:
        time.sleep(60)

if __name__ == "__main__":
    recover()
