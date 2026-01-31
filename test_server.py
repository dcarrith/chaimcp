import unittest
from unittest.mock import patch, MagicMock
import json
import sys
import os

# Add src to path
sys.path.append(os.path.abspath("src"))

from chaimcp.main import mcp, get_blockchain_state, get_wallet_balance

class TestChaiMCP(unittest.TestCase):
    


    @patch("chaimcp.main.ChiaRpcClient")
    def test_get_blockchain_state(self, MockClient):
        """Test get_blockchain_state tool."""
        # Setup mock
        mock_instance = MockClient.return_value
        mock_instance.get_blockchain_state.return_value = {
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
        self.assertTrue(data["synced"])
        self.assertEqual(data["peak_height"], 12345)

    @patch("chaimcp.main.ChiaRpcClient")
    def test_get_wallet_balance(self, MockClient):
        """Test get_wallet_balance tool."""
        # Setup mock
        mock_instance = MockClient.return_value
        mock_instance.get_wallet_balance.return_value = {
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
        self.assertEqual(data["confirmed_balance_xch"], 1.5)

if __name__ == "__main__":
    unittest.main()
