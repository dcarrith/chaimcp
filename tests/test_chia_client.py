import unittest
from unittest.mock import patch, MagicMock
import requests
from chaimcp.chia_client import ChiaRpcClient

class TestChiaRpcClient(unittest.TestCase):

    @patch("chaimcp.chia_client.load_chia_config")
    @patch("chaimcp.chia_client.get_ssl_paths")
    @patch("chaimcp.chia_client.get_chia_root")
    def setUp(self, mock_get_root, mock_get_ssl, mock_load_config):
        self.mock_config = {
            "full_node": {"rpc_port": 8555},
            "wallet": {"rpc_port": 9256}
        }
        mock_load_config.return_value = self.mock_config
        mock_get_ssl.return_value = {"cert": "c", "key": "k", "ca": "ca"}
        
        self.client = ChiaRpcClient("full_node")

    def test_init_defaults(self):
        """Test initialization with default ports from config."""
        self.assertEqual(self.client.port, 8555)
        
        # Test wallet default
        with patch("chaimcp.chia_client.load_chia_config", return_value=self.mock_config), \
             patch("chaimcp.chia_client.get_ssl_paths", return_value={"cert":"c", "key":"k"}):
            wallet_client = ChiaRpcClient("wallet")
            self.assertEqual(wallet_client.port, 9256)

    def test_init_unknown_service(self):
        """Test error when unknown service used without explicit port."""
        with patch("chaimcp.chia_client.load_chia_config", return_value=self.mock_config), \
             patch("chaimcp.chia_client.get_ssl_paths", return_value={"cert":"c", "key":"k"}):
            with self.assertRaises(ValueError):
                ChiaRpcClient("unknown_service")

    def test_init_explicit_port(self):
        """Test initialization with explicit port override."""
        with patch("chaimcp.chia_client.load_chia_config"), \
             patch("chaimcp.chia_client.get_ssl_paths", return_value={"cert":"c", "key":"k"}):
            client = ChiaRpcClient("full_node", port=1234)
            self.assertEqual(client.port, 1234)

    @patch("requests.Session.post")
    def test_get_success(self, mock_post):
        """Test successful RPC call."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"success": True, "foo": "bar"}
        mock_post.return_value = mock_response

        # We need to re-init client locally to mock session properly or just patch the existing one
        # Here we rely on self.client created in setUp, which already has a session.
        # But requests.Session() is instantiated in __init__.
        # So we patch the method on the class or instance.
        
        res = self.client.get("test_endpoint", {"data": 1})
        self.assertEqual(res["success"], True)
        self.assertEqual(res["foo"], "bar")
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        self.assertTrue("https://localhost:8555/test_endpoint" in args[0])
        self.assertEqual(kwargs["json"], {"data": 1})

    @patch("requests.Session.post")
    def test_get_connection_error(self, mock_post):
        """Test handling of ConnectionError."""
        mock_post.side_effect = requests.exceptions.ConnectionError("Connection refused")
        
        res = self.client.get("test_endpoint")
        self.assertFalse(res["success"])
        self.assertIn("Connection refused", res["error"])

    @patch("requests.Session.post")
    def test_get_generic_exception(self, mock_post):
        """Test handling of generic exceptions."""
        mock_post.side_effect = Exception("Boom")
        
        res = self.client.get("test_endpoint")
        self.assertFalse(res["success"])
        self.assertEqual(res["error"], "Boom")
        
    @patch("chaimcp.chia_client.ChiaRpcClient.get")
    def test_wrappers(self, mock_get):
        """Test convenience wrapper methods."""
        self.client.get_blockchain_state()
        mock_get.assert_called_with("get_blockchain_state")
        
        self.client.get_network_info()
        mock_get.assert_called_with("get_network_info")
        
        self.client.get_wallets()
        mock_get.assert_called_with("get_wallets")
        
        self.client.get_wallet_balance(123)
        mock_get.assert_called_with("get_wallet_balance", {"wallet_id": 123})
