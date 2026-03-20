import urllib.request
try:
    req = urllib.request.Request("http://127.0.0.1:8889/.well-known/oauth-authorization-server")
    with urllib.request.urlopen(req) as response:
        print("STATUS:", response.status)
        print("BODY:", response.read().decode())
except Exception as e:
    print("ERR:", e)
