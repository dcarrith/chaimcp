from mcp.server.fastmcp import FastMCP
from .chia_client import ChiaRpcClient
import json

# Initialize FastMCP server
mcp = FastMCP("chaimcp")

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
    mcp.run()

if __name__ == "__main__":
    main()
