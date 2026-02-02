import subprocess # nosec
import time
import sys

def run_test():
    # Start port-forward
    pf = subprocess.Popen(["kubectl", "port-forward", "svc/chiamcp", "8000:8000"], stdout=subprocess.PIPE, stderr=subprocess.PIPE) # nosec
    time.sleep(3) # Wait for connection

    try:
        print("Testing without token...")
        try:
            res = subprocess.run(["curl", "-i", "-s", "-o", "/dev/null", "-w", "%{http_code}", "http://localhost:8000/sse"], capture_output=True, text=True, timeout=5) # nosec
            print(f"No Token Response Code: {res.stdout.strip()}")
            if res.stdout.strip() in ["401", "403"]:
                print("PASS: Request without token rejected.")
            else:
                print(f"FAIL: Expected 401/403, got {res.stdout.strip()}")
        except subprocess.TimeoutExpired:
            print("FAIL: Timeout without token (should reject fast).")

        print("\nTesting with valid token...")
        try:
            # We use timeout=2 because success means stream opens (hangs)
            subprocess.run(["curl", "-i", "-H", "Authorization: Bearer my-secret-token", "http://localhost:8000/sse"], timeout=2, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) # nosec
            print("FAIL: Connection closed immediately (unexpected for SSE).")
        except subprocess.TimeoutExpired:
             # Timeout is GOOD for SSE stream!
             print("PASS: Connection established and held open (SSE stream).")
        except Exception as e:
            print(f"Error: {e}")

    finally:
        pf.terminate()
        print("\nPort-forward terminated.")

if __name__ == "__main__":
    run_test()
