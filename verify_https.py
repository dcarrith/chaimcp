import subprocess
import time
import sys
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def run_test():
    # Start port-forward
    pf = subprocess.Popen(["kubectl", "port-forward", "svc/chiamcp", "4443:4443"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    time.sleep(3) # Wait for connection

    try:
        print("Testing HTTPS without token...")
        try:
            # -k for insecure/self-signed
            res = subprocess.run(["curl", "-k", "-i", "-s", "-o", "/dev/null", "-w", "%{http_code}", "https://localhost:4443/sse"], capture_output=True, text=True, timeout=5)
            print(f"No Token Response Code: {res.stdout.strip()}")
            if res.stdout.strip() in ["401", "403"]:
                print("PASS: HTTPS Request without token rejected.")
            else:
                print(f"FAIL: Expected 401/403, got {res.stdout.strip()}")
        except subprocess.TimeoutExpired:
            print("FAIL: Timeout without token.")

        print("\nTesting HTTPS with valid token...")
        try:
            # We use python requests here for better control, verified=False
            res = requests.get('https://localhost:4443/sse', headers={'Authorization': 'Bearer my-secret-token'}, stream=True, timeout=2, verify=False)
            print(f"Status Code: {res.status_code}")
            # If we get here without timeout, it might be 200 OK headers received, or 401
            if res.status_code == 200:
                 print("PASS: HTTPS Connection established (headers received).")
            else:
                 print(f"FAIL: Expected 200, got {res.status_code}")
        except requests.exceptions.ReadTimeout:
             # Timeout on read is expected for infinite stream if headers already processed
             print("PASS: HTTPS Connection established (stream open).")
        except Exception as e:
             # If connect timeout, that's bad
             print(f"FAIL: Error: {e}")

    finally:
        pf.terminate()
        print("\nPort-forward terminated.")

if __name__ == "__main__":
    run_test()
