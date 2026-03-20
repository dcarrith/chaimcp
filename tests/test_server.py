import unittest
from unittest.mock import patch, MagicMock
import json
import sys
import os

# Add src to path
sys.path.append(os.path.abspath("src"))

from chaimcp.main import mcp, get_blockchain_state, get_wallet_balance, EnvTokenVerifier

class TestAuth(unittest.IsolatedAsyncioTestCase):
    async def test_valid_token(self):
        """Test EnvTokenVerifier with valid token."""
        verifier = EnvTokenVerifier("secret-token")
        token = await verifier.verify_token("secret-token")
        self.assertIsNotNone(token)
        self.assertEqual(token.token, "secret-token")
        self.assertEqual(token.client_id, "unknown")

    async def test_invalid_token(self):
        """Test EnvTokenVerifier with invalid token."""
        verifier = EnvTokenVerifier("secret-token")
        token = await verifier.verify_token("wrong-token")
        self.assertIsNone(token)

class TestChaiMCP(unittest.TestCase):
    def setUp(self):
        self.config_patcher = patch("chaimcp.chia_client.load_chia_config", return_value={"selected_network": "mainnet", "full_node": {"port": 8555}, "wallet": {"port": 9256}})
        self.mock_config = self.config_patcher.start()
        
    def tearDown(self):
        self.config_patcher.stop()
    
    @patch("chaimcp.chia_client.ChiaRpcClient.get_blockchain_state")
    def test_get_blockchain_state(self, mock_get):
        """Test get_blockchain_state tool."""
        # Setup mock
        mock_get.return_value = {
            "success": True,
            "blockchain_state": {
                "sync": {"sync_mode": False, "synced": True},
                "peak": {"height": 12345},
                "difficulty": 100
            }
        }
        
        # Run tool
        result = get_blockchain_state()
        data = json.loads(result)
        
        # Verify
        self.assertTrue(data["blockchain_state"]["sync"]["synced"])
        self.assertEqual(data["blockchain_state"]["peak"]["height"], 12345)

    @patch("chaimcp.chia_client.ChiaRpcClient.get_wallet_balance")
    def test_get_wallet_balance(self, mock_get):
        """Test get_wallet_balance tool."""
        # Setup mock
        mock_get.return_value = {
            "success": True,
            "wallet_balance": {
                "confirmed_wallet_balance": 1500000000000, # 1.5 XCH
                "spendable_balance": 1500000000000
            }
        }
        
        # Run tool
        result = get_wallet_balance(1)
        data = json.loads(result)
        
        # Verify
        self.assertEqual(data["wallet_balance"]["confirmed_wallet_balance"], 1500000000000)

if __name__ == "__main__":
    unittest.main()
