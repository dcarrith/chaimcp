from mcp.server.fastmcp import FastMCP
from mcp.server.auth.settings import AuthSettings
from mcp.server.auth.provider import TokenVerifier, AccessToken
from .chia_client import ChiaRpcClient
import json
import os

# --- Authentication ---

class EnvTokenVerifier:
    def __init__(self, token: str):
        self.token = token

    async def verify_token(self, token: str) -> AccessToken | None:
        if token == self.token:
            return AccessToken(
                token=token,
                client_id="unknown",
                scopes=[],
            )
        return None

auth_token = os.environ.get("MCP_AUTH_TOKEN")
auth_settings = None
token_verifier = None

if auth_token:
    # We must provide AuthSettings if we provide a verifier, even if we don't use the issuer/resource_url logic
    auth_settings = AuthSettings(
        issuer_url="http://localhost",
        resource_server_url="http://localhost",
    )
    token_verifier = EnvTokenVerifier(auth_token)

# Initialize FastMCP server
mcp = FastMCP(
    "chaimcp",
    auth=auth_settings,
    token_verifier=token_verifier
)

# --- Full Node Tools ---

@mcp.tool()
def get_blockchain_state() -> str:
    """
    Get the current state of the blockchain (sync status, peak height, difficulty).
    Returns a JSON string summary.
    """
    client = ChiaRpcClient("full_node")
    state = client.get_blockchain_state()
    
    if not state.get("success"):
        return f"Error: {state.get('error')}"
        
    blockchain_state = state.get("blockchain_state", {})
    summary = {
        "sync_mode": blockchain_state.get("sync", {}).get("sync_mode"),
        "synced": blockchain_state.get("sync", {}).get("synced"),
        "peak_height": blockchain_state.get("peak", {}).get("height"),
        "space": blockchain_state.get("space"),
        "difficulty": blockchain_state.get("difficulty")
    }
    return json.dumps(summary, indent=2)

@mcp.tool()
def get_network_info() -> str:
    """Get network name and prefix (e.g., mainnet, xch)."""
    client = ChiaRpcClient("full_node")
    info = client.get_network_info()
    return json.dumps(info, indent=2)

# --- Wallet Tools ---

@mcp.tool()
def get_wallet_balance(wallet_id: int = 1) -> str:
    """
    Get the balance of a specific wallet.
    Args:
        wallet_id: The ID of the wallet (default: 1 for XCH).
    """
    client = ChiaRpcClient("wallet")
    balance = client.get_wallet_balance(wallet_id)
    
    if not balance.get("success"):
        return f"Error: {balance.get('error')}"
        
    wallet_balance = balance.get("wallet_balance", {})
    # Convert mojos to XCH for display (1 XCH = 1,000,000,000,000 mojos)
    confirmed_wallet_balance = wallet_balance.get("confirmed_wallet_balance", 0)
    xch_balance = confirmed_wallet_balance / 1e12
    
    summary = {
        "wallet_id": wallet_id,
        "confirmed_balance_mojos": confirmed_wallet_balance,
        "confirmed_balance_xch": xch_balance,
        "spendable_balance_mojos": wallet_balance.get("spendable_balance", 0)
    }
    return json.dumps(summary, indent=2)

def main():
    """Entry point for the application script."""
    transport = os.environ.get("MCP_TRANSPORT", "stdio")
    print(f"Starting ChaiMCP server with transport: {transport}")

    if transport in ["sse", "http"]:
        import uvicorn
        
        # Get settings from environment
        port = int(os.environ.get("MCP_PORT", 8000))
        host = "0.0.0.0" # nosec
        ssl_keyfile = os.environ.get("SSL_KEY_FILE", "/app/server.key")
        ssl_certfile = os.environ.get("SSL_CERT_FILE", "/app/server.crt")
        
        # Check if SSL files exist
        ssl_config = {}
        if os.path.exists(ssl_keyfile) and os.path.exists(ssl_certfile):
             print(f"SSL enabled. Using cert: {ssl_certfile}")
             ssl_config = {
                 "ssl_keyfile": ssl_keyfile,
                 "ssl_certfile": ssl_certfile
             }
        else:
             print("SSL files not found, running HTTP only.")

        if transport == "sse":
            starlette_app = mcp.sse_app()
        else:
            # transport == "http"
            starlette_app = mcp.streamable_http_app()
        
        uvicorn.run(
            starlette_app, 
            host=host, 
            port=port, 
            **ssl_config
        )
    else:
        mcp.run(transport=transport)

if __name__ == "__main__": # pragma: no cover
    print("ChaiMCP module loaded")
    main()
