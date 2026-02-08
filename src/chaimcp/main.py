from mcp.server.fastmcp import FastMCP
from mcp.server.auth.settings import AuthSettings
from mcp.server.auth.provider import TokenVerifier, AccessToken
from .config import get_mcp_auth_enabled
from .chia_client import ChiaRpcClient
import json
import os

from mcp.server.transport_security import TransportSecuritySettings

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

if get_mcp_auth_enabled() and auth_token:
    # We must provide AuthSettings if we provide a verifier, even if we don't use the issuer/resource_url logic
    auth_settings = AuthSettings(
        issuer_url="http://localhost",
        resource_server_url="http://localhost",
    )
    token_verifier = EnvTokenVerifier(auth_token)

# Configure Transport Security
# We enable DNS rebinding protection but allow the specific host used by Ingress
transport_security = TransportSecuritySettings(
    enable_dns_rebinding_protection=True,
    allowed_hosts=["localhost", "127.0.0.1", "mcpch.ai:*", "mcpch.ai"],
    allowed_origins=["http://localhost", "http://127.0.0.1", "https://mcpch.ai"]
)

# Initialize FastMCP server
mcp = FastMCP(
    "chaimcp",
    auth=auth_settings,
    token_verifier=token_verifier,
    transport_security=transport_security,
    host="0.0.0.0" # Bind to all interfaces to receive Ingress traffic
)

# --- Tool Registration Helper ---

def register_tool(name: str = None, description: str = None):
    """
    Decorator to register a tool with FastMCP, unless it is listed in MCP_DISABLED_TOOLS.
    """
    def decorator(func):
        tool_name = name or func.__name__
        disabled_tools_str = os.environ.get("MCP_DISABLED_TOOLS", "")
        # Parse comma-separated list, stripping whitespace
        disabled_tools = [t.strip() for t in disabled_tools_str.split(",") if t.strip()]
        
        if tool_name in disabled_tools:
            print(f"Disabled tool: {tool_name}")
            return func
            
        return mcp.tool(name=name, description=description)(func)
    return decorator

# --- Full Node Tools ---

@register_tool()
def get_blockchain_state() -> str:
    """
    Get the current state of the blockchain (sync status, peak height, difficulty).
    """
    client = ChiaRpcClient("full_node")
    return json.dumps(client.get_blockchain_state(), indent=2)

@register_tool()
def get_network_info() -> str:
    """Get network name and prefix (e.g., mainnet, xch)."""
    client = ChiaRpcClient("full_node")
    return json.dumps(client.get_network_info(), indent=2)

@register_tool()
def get_block_record_by_height(height: int) -> str:
    """Get a block record by its height."""
    client = ChiaRpcClient("full_node")
    return json.dumps(client.get("get_block_record_by_height", {"height": height}), indent=2)

@register_tool()
def get_block_record(header_hash: str) -> str:
    """Get a block record by its header hash."""
    client = ChiaRpcClient("full_node")
    return json.dumps(client.get("get_block_record", {"header_hash": header_hash}), indent=2)

@register_tool()
def get_coin_records_by_puzzle_hash(puzzle_hash: str, start_height: int = None, end_height: int = None, include_spent_coins: bool = False) -> str:
    """Get coin records for a puzzle hash."""
    data = {"puzzle_hash": puzzle_hash, "include_spent_coins": include_spent_coins}
    if start_height is not None: data["start_height"] = start_height
    if end_height is not None: data["end_height"] = end_height
    client = ChiaRpcClient("full_node")
    return json.dumps(client.get("get_coin_records_by_puzzle_hash", data), indent=2)

@register_tool()
def get_coin_records_by_parent_ids(parent_ids: list[str], start_height: int = None, end_height: int = None, include_spent_coins: bool = False) -> str:
    """Get coin records by parent coin IDs."""
    data = {"parent_ids": parent_ids, "include_spent_coins": include_spent_coins}
    if start_height is not None: data["start_height"] = start_height
    if end_height is not None: data["end_height"] = end_height
    client = ChiaRpcClient("full_node")
    return json.dumps(client.get("get_coin_records_by_parent_ids", data), indent=2)

@register_tool()
def push_tx(spend_bundle: dict) -> str:
    """Push a transaction spend bundle to the network."""
    client = ChiaRpcClient("full_node")
    return json.dumps(client.get("push_tx", {"spend_bundle": spend_bundle}), indent=2)

@register_tool()
def get_all_mempool_tx_ids() -> str:
    """Get all transaction IDs currently in the mempool."""
    client = ChiaRpcClient("full_node")
    return json.dumps(client.get("get_all_mempool_tx_ids"), indent=2)

@register_tool()
def get_mempool_item_by_tx_id(tx_id: str) -> str:
    """Get a mempool item by transaction ID."""
    client = ChiaRpcClient("full_node")
    return json.dumps(client.get("get_mempool_item_by_tx_id", {"tx_id": tx_id}), indent=2)

# --- Wallet Tools ---

@register_tool()
def get_wallet_balance(wallet_id: int = 1) -> str:
    """Get the balance of a specific wallet."""
    client = ChiaRpcClient("wallet")
    return json.dumps(client.get_wallet_balance(wallet_id), indent=2)

@register_tool()
def get_wallets(type: int = None) -> str:
    """Get a list of wallets."""
    data = {}
    if type is not None: data["type"] = type
    client = ChiaRpcClient("wallet")
    return json.dumps(client.get("get_wallets", data), indent=2)

@register_tool()
def get_transactions(wallet_id: int = 1, start: int = 0, end: int = 50, reverse: bool = False) -> str:
    """Get transactions for a wallet."""
    data = {"wallet_id": wallet_id, "start": start, "end": end, "reverse": reverse}
    client = ChiaRpcClient("wallet")
    return json.dumps(client.get("get_transactions", data), indent=2)

@register_tool()
def get_transaction(transaction_id: str) -> str:
    """Get full details of a specific transaction."""
    client = ChiaRpcClient("wallet")
    return json.dumps(client.get("get_transaction", {"transaction_id": transaction_id}), indent=2)

@register_tool()
def send_transaction(wallet_id: int, amount: int, address: str, fee: int = 0) -> str:
    """Send a transaction (amount in mojos)."""
    data = {"wallet_id": wallet_id, "amount": amount, "address": address, "fee": fee}
    client = ChiaRpcClient("wallet")
    return json.dumps(client.get("send_transaction", data), indent=2)

@register_tool()
def get_next_address(wallet_id: int = 1, new_address: bool = True) -> str:
    """Get the next address for a wallet."""
    data = {"wallet_id": wallet_id, "new_address": new_address}
    client = ChiaRpcClient("wallet")
    return json.dumps(client.get("get_next_address", data), indent=2)

@register_tool()
def get_farmed_amount() -> str:
    """Get the total amount farmed."""
    client = ChiaRpcClient("wallet")
    return json.dumps(client.get("get_farmed_amount"), indent=2)

# --- Key Management Tools (High Security Risk - Disable via MCP_DISABLED_TOOLS) ---

@register_tool()
def generate_mnemonic() -> str:
    """Generate a new 24-word mnemonic."""
    client = ChiaRpcClient("wallet")
    return json.dumps(client.get("generate_mnemonic"), indent=2)

@register_tool()
def add_key(mnemonic: list[str]) -> str:
    """Add a key from mnemonic."""
    client = ChiaRpcClient("wallet")
    return json.dumps(client.get("add_key", {"mnemonic": mnemonic}), indent=2)

@register_tool()
def delete_key(fingerprint: int) -> str:
    """Delete a key by fingerprint."""
    client = ChiaRpcClient("wallet")
    return json.dumps(client.get("delete_key", {"fingerprint": fingerprint}), indent=2)

@register_tool()
def delete_all_keys() -> str:
    """Delete all keys from the keychain."""
    client = ChiaRpcClient("wallet")
    return json.dumps(client.get("delete_all_keys"), indent=2)

# --- Datalayer Tools ---

@register_tool()
def create_data_store(fee: int = 0) -> str:
    """Create a new Datalayer store."""
    client = ChiaRpcClient("data_layer")
    return json.dumps(client.get("create_data_store", {"fee": fee}), indent=2)

@register_tool()
def get_value(store_id: str, key: str, root_hash: str = None) -> str:
    """Get a value from a Datalayer store."""
    data = {"id": store_id, "key": key}
    if root_hash: data["root_hash"] = root_hash
    client = ChiaRpcClient("data_layer")
    return json.dumps(client.get("get_value", data), indent=2)

@register_tool()
def update_data_store(store_id: str, changelist: list[dict], fee: int = 0) -> str:
    """
    Update a Datalayer store.
    changelist format: [{"action": "insert", "key": "hex", "value": "hex"}, ...]
    """
    client = ChiaRpcClient("data_layer")
    return json.dumps(client.get("update_data_store", {"id": store_id, "changelist": changelist, "fee": fee}), indent=2)

@register_tool()
def get_keys(store_id: str, root_hash: str = None) -> str:
    """Get all keys for a Datalayer store."""
    data = {"id": store_id}
    if root_hash: data["root_hash"] = root_hash
    client = ChiaRpcClient("data_layer")
    return json.dumps(client.get("get_keys", data), indent=2)

@register_tool()
def get_root(store_id: str) -> str:
    """Get the current root hash of a store."""
    client = ChiaRpcClient("data_layer")
    return json.dumps(client.get("get_root", {"id": store_id}), indent=2)

@register_tool()
def subscribe(store_id: str, urls: list[str] = []) -> str:
    """Subscribe to a Datalayer store."""
    client = ChiaRpcClient("data_layer")
    return json.dumps(client.get("subscribe", {"id": store_id, "urls": urls}), indent=2)

@register_tool()
def unsubscribe(store_id: str) -> str:
    """Unsubscribe from a Datalayer store."""
    client = ChiaRpcClient("data_layer")
    return json.dumps(client.get("unsubscribe", {"id": store_id}), indent=2)

@register_tool()
def get_kv_diff(store_id: str, hash_1: str, hash_2: str) -> str:
    """Get the key-value difference between two root hashes."""
    client = ChiaRpcClient("data_layer")
    return json.dumps(client.get("get_kv_diff", {"id": store_id, "hash_1": hash_1, "hash_2": hash_2}), indent=2)

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
