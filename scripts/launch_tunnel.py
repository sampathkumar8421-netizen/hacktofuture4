import time
import os
import sys
from pyngrok import ngrok

# Attempt to load ngrok token from environment if available
NGROK_TOKEN = os.getenv("NGROK_AUTHTOKEN")

if NGROK_TOKEN:
    ngrok.set_auth_token(NGROK_TOKEN)
    print("[Ngrok] Auth token set from environment.")
else:
    print("[Ngrok] Warning: No NGROK_AUTHTOKEN found in environment. Using anonymous tunnel (if permitted).")

try:
    # Open a HTTP tunnel on port 8000
    public_url = ngrok.connect(8000).public_url
    print(f"\n[OK] Lily02 Public Tunnel Active!")
    print(f"URL: {public_url}")
    print("-" * 40)
    print("Keep this script running to maintain the tunnel.")
    
    # Keep the script alive
    while True:
        time.sleep(10)
except Exception as e:
    print(f"[Error] Failed to create ngrok tunnel: {e}")
    sys.exit(1)
except KeyboardInterrupt:
    print("\n[Ngrok] Closing tunnel...")
    ngrok.kill()
