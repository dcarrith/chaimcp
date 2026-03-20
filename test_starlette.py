import os
os.environ["MCP_TRANSPORT"] = "http"
from src.chaimcp.main import mcp
app = mcp.streamable_http_app()

from starlette.testclient import TestClient
client = TestClient(app)
response = client.get("/.well-known/oauth-authorization-server")
print("STATUS:", response.status_code)
print("BODY:", response.text)
