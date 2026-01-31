import requests
import urllib3
from typing import Dict, Any, Optional
from .config import get_chia_root, load_chia_config, get_ssl_paths

# Suppress insecure request warnings if verifying is disabled (though we should try to verify)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class ChiaRpcClient:
    def __init__(self, service_name: str, port: int = None):
        self.service_name = service_name
        self.root_path = get_chia_root()
        self.config = load_chia_config(self.root_path)
        self.ssl_paths = get_ssl_paths(service_name, self.root_path)
        
        # Determine port if not provided
        if port is None:
            if service_name == "full_node":
                self.port = self.config.get("full_node", {}).get("rpc_port", 8555)
            elif service_name == "wallet":
                self.port = self.config.get("wallet", {}).get("rpc_port", 9256)
            else:
                raise ValueError(f"Unknown default port for service: {service_name}")
        else:
            self.port = port
            
        self.base_url = f"https://localhost:{self.port}"
        self.session = requests.Session()
        self.session.cert = (self.ssl_paths["cert"], self.ssl_paths["key"])
        self.session.verify = False # Self-signed certs are the norm for localhost Chia, usually verified against CA but False is easier for MVP

    def get(self, endpoint: str, data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Generic RPC POST request (Chia RPCs use POST)."""
        url = f"{self.base_url}/{endpoint}"
        try:
            response = self.session.post(url, json=data or {}, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.ConnectionError:
            return {"success": False, "error": f"Connection refused to {self.service_name} at port {self.port}. Is it running?"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # --- Common Full Node Methods ---
    def get_blockchain_state(self):
        return self.get("get_blockchain_state")
        
    def get_network_info(self):
        return self.get("get_network_info")

    # --- Common Wallet Methods ---
    def get_wallets(self):
        return self.get("get_wallets")
        
    def get_wallet_balance(self, wallet_id: int):
        return self.get("get_wallet_balance", {"wallet_id": wallet_id})
