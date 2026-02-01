import subprocess
import time
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def run_test():
    # Forward local 4443 to service port 443
    pf = subprocess.Popen(["kubectl", "port-forward", "svc/chaimcp", "4443:443"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    time.sleep(3)

    try:
        print("Testing HTTPS via renamed service (chaimcp)...")
        # -k for insecure
        res = requests.get('https://localhost:4443/sse', verify=False, timeout=2)
        print(f"Status: {res.status_code}")
        if res.status_code == 401:
             print("PASS: Service reachable, Auth required.")
        else:
             print(f"FAIL: Unexpected status {res.status_code}")
             
    except Exception as e:
        print(f"FAIL: {e}")
    finally:
        pf.terminate()

if __name__ == "__main__":
    run_test()
