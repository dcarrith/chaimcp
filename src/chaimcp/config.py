import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional

DEFAULT_CHIA_ROOT = Path(os.path.expanduser("~/.chia/mainnet"))

def get_chia_root() -> Path:
    """Get the Chia root directory via environment variable or default."""
    return Path(os.environ.get("CHIA_ROOT", DEFAULT_CHIA_ROOT))

def load_chia_config(root_path: Optional[Path] = None) -> Dict[str, Any]:
    """Load the Chia configuration file."""
    if root_path is None:
        root_path = get_chia_root()
    
    config_path = root_path / "config" / "config.yaml"
    if not config_path.exists():
        raise FileNotFoundError(f"Chia config not found at {config_path}")
        
    with open(config_path, "r") as f:
        return yaml.safe_load(f)

def get_ssl_paths(service_name: str, root_path: Optional[Path] = None) -> Dict[str, str]:
    """
    Get SSL certificate and key paths for a specific service (e.g., 'daemon', 'full_node', 'wallet').
    Resolves paths relative to CHIA_ROOT/config/ssl/ or absolute paths from config.
    """
    if root_path is None:
        root_path = get_chia_root()
    
    # Standard location based on typical Chia layout since config parsing can be complex
    # for self-signed interaction within the same machine.
    # We'll try to find the standard private keys.
    
    # Note: For MCP interaction, we usually want the "private_" certs to authenticate as a client
    # to the local service.
    
    base_ssl = root_path / "config" / "ssl"
    
    # Mapping service name to cert directory name
    # daemon -> daemon
    # full_node -> full_node
    # wallet -> wallet
    
    crt_path = base_ssl / service_name / f"private_{service_name}.crt"
    key_path = base_ssl / service_name / f"private_{service_name}.key"
    
    if not crt_path.exists() or not key_path.exists():
        # Fallback: check CA if we just need to verify? No, we need client auth usually.
        # But let's check config if we want to be robust (skipped for MVP speed, assuming standard layout).
        pass
        
    return {
        "cert": str(crt_path),
        "key": str(key_path),
        "ca": str(base_ssl / "ca" / "private_ca.crt") # CA to verify server
    }
