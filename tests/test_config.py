import os
import unittest
from unittest.mock import patch, mock_open, MagicMock
from pathlib import Path
from chaimcp.config import get_chia_root, load_chia_config, get_ssl_paths

class TestConfig(unittest.TestCase):

    @patch.dict(os.environ, {"CHIA_ROOT": "/custom/chia/root"})
    def test_get_chia_root_env_var(self):
        """Test getting CHIA_ROOT from environment variable."""
        root = get_chia_root()
        self.assertEqual(str(root), "/custom/chia/root")

    @patch.dict(os.environ, {}, clear=True)
    def test_get_chia_root_default(self):
        """Test getting default CHIA_ROOT when env var is not set."""
        # Note: This relies on the DEFAULT_CHIA_ROOT import in config.py
        # which expands ~/.chia/mainnet. We check if it ends with .chia/mainnet
        root = get_chia_root()
        self.assertTrue(str(root).endswith(".chia/mainnet"))

    @patch("pathlib.Path.exists")
    def test_load_chia_config_not_found(self, mock_exists):
        """Test FileNotFoundError when config file is missing."""
        mock_exists.return_value = False
        with self.assertRaises(FileNotFoundError):
            load_chia_config(Path("/dummy/root"))

    @patch("pathlib.Path.exists")
    @patch("builtins.open", new_callable=mock_open, read_data="full_node:\n  rpc_port: 8555")
    def test_load_chia_config_success(self, mock_file, mock_exists):
        """Test successfully loading valid YAML config."""
        mock_exists.return_value = True
        config = load_chia_config(Path("/dummy/root"))
        self.assertEqual(config["full_node"]["rpc_port"], 8555)

    @patch("pathlib.Path.exists")
    @patch("builtins.open", new_callable=mock_open, read_data="wallet:\n  rpc_port: 9256")
    @patch("chaimcp.config.get_chia_root")
    def test_load_chia_config_implicit_root(self, mock_get_root, mock_file, mock_exists):
        """Test laoding config using implicit get_chia_root()."""
        mock_get_root.return_value = Path("/implicit/root")
        mock_exists.return_value = True
        config = load_chia_config()
        self.assertEqual(config["wallet"]["rpc_port"], 9256)
        mock_get_root.assert_called_once()

    @patch("pathlib.Path.exists")
    def test_get_ssl_paths(self, mock_exists):
        """Test SSL path generation."""
        mock_exists.return_value = True
        root = Path("/test/root")
        paths = get_ssl_paths("full_node", root)
        
        base = "/test/root/config/ssl/full_node"
        self.assertEqual(paths["cert"], f"{base}/private_full_node.crt")
        self.assertEqual(paths["key"], f"{base}/private_full_node.key")
        self.assertTrue(paths["ca"].endswith("private_ca.crt"))

    @patch("chaimcp.config.get_chia_root")
    @patch("pathlib.Path.exists")
    def test_get_ssl_paths_implicit_root(self, mock_exists, mock_get_root):
        """Test SSL path generation with implicit root."""
        mock_exists.return_value = True
        mock_get_root.return_value = Path("/implicit/root")
        
        paths = get_ssl_paths("wallet")
        base = "/implicit/root/config/ssl/wallet"
        self.assertEqual(paths["cert"], f"{base}/private_wallet.crt")
