import http.server
import socketserver
import requests
import os
import sys

# Configuration
LOCAL_PORT = 8001
TARGET_URL = "https://localhost:4443/sse"
AUTH_TOKEN = os.environ.get("AUTH_TOKEN", "my-secret-token") # nosec

class ProxyHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        # Forward the GET request to the target HTTPS server
        try:
            print(f"Proxying GET {self.path} to {TARGET_URL}")
            
            # Prepare headers
            headers = {key: val for key, val in self.headers.items()}
            # headers['Host'] = 'localhost:4443' # Usually requests handles this
            
            # Make the request to the backend (insecure=True)
            resp = requests.get(
                TARGET_URL, 
                headers=headers, 
                stream=True, 
                verify=False, # nosec
                timeout=None
            )
            
            # Send response status code
            self.send_response(resp.status_code)
            
            # Send headers
            for key, val in resp.headers.items():
                if key.lower() not in ['transfer-encoding', 'content-encoding', 'connection']:
                    self.send_header(key, val)
            self.end_headers()
            
            # Stream content
            for chunk in resp.iter_content(chunk_size=8192):
                if chunk:
                    self.wfile.write(chunk)
                    self.wfile.flush()
                    
        except Exception as e:
            print(f"Proxy Error: {e}")
            self.send_error(502, f"Bad Gateway: {e}")

    def do_POST(self):
         # Forward POST requests (for future JSON-RPC usage)
        try:
            length = int(self.headers.get('content-length', 0))
            body = self.rfile.read(length) if length > 0 else None
            
            print(f"Proxying POST {self.path} to {TARGET_URL}")

            headers = {key: val for key, val in self.headers.items()}
            
            resp = requests.post(
                TARGET_URL.replace("/sse", self.path), # Adjust path if needed
                data=body,
                headers=headers,
                stream=True,
                verify=False # nosec
            )
             
            self.send_response(resp.status_code)
            for key, val in resp.headers.items():
                if key.lower() not in ['transfer-encoding', 'content-encoding', 'connection']:
                     self.send_header(key, val)
            self.end_headers()
            
            for chunk in resp.iter_content(chunk_size=8192):
                 if chunk:
                     self.wfile.write(chunk)
                     self.wfile.flush()

        except Exception as e:
            print(f"Error: {e}")
            self.send_error(502, f"Bad Gateway: {e}")

if __name__ == "__main__":
    print(f"Starting TLS Bridge on http://localhost:{LOCAL_PORT}")
    print(f"Forwarding to {TARGET_URL} (Insecure)")
    
    # Allow address reuse
    socketserver.TCPServer.allow_reuse_address = True
    
    with socketserver.TCPServer(("localhost", LOCAL_PORT), ProxyHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down bridge.")
