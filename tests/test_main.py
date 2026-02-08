import sys
import subprocess
import unittest
from importlib import reload
from unittest.mock import patch, MagicMock, AsyncMock
import os
import json
import chaimcp.main as main_module
from chaimcp.main import get_blockchain_state, get_network_info, get_wallet_balance, EnvTokenVerifier

class TestMain(unittest.TestCase):

    def test_env_token_verifier(self):
        """Test validation of tokens."""
        verifier = EnvTokenVerifier("secret_token")
        
        # Helper to run async method
        import asyncio
        loop = asyncio.new_event_loop()
        
        valid = loop.run_until_complete(verifier.verify_token("secret_token"))
        self.assertIsNotNone(valid)
        self.assertEqual(valid.token, "secret_token")
        
        invalid = loop.run_until_complete(verifier.verify_token("wrong"))
        self.assertIsNone(invalid)
        loop.close()

    @patch("chaimcp.main.ChiaRpcClient")
    def test_tool_get_blockchain_state_success(self, MockClient):
        """Test get_blockchain_state tool success path."""
        mock_instance = MockClient.return_value
        mock_instance.get_blockchain_state.return_value = {
            "success": True,
            "blockchain_state": {
                "sync": {"sync_mode": True, "synced": True},
                "peak": {"height": 100},
                "space": 1000,
                "difficulty": 5
            }
        }
        
        result = get_blockchain_state()
        data = json.loads(result)
        # New implementation returns full blockchain_state object inside the response
        self.assertEqual(data["blockchain_state"]["peak"]["height"], 100)
        self.assertTrue(data["blockchain_state"]["sync"]["synced"])

    @patch("chaimcp.main.ChiaRpcClient")
    def test_tool_get_blockchain_state_failure(self, MockClient):
        """Test get_blockchain_state tool failure path."""
        mock_instance = MockClient.return_value
        mock_instance.get_blockchain_state.return_value = {
            "success": False,
            "error": "RPC Error"
        }
        
        result = get_blockchain_state()
        data = json.loads(result)
        self.assertFalse(data["success"])
        self.assertEqual(data["error"], "RPC Error")

    @patch("chaimcp.main.ChiaRpcClient")
    def test_tool_get_network_info(self, MockClient):
        """Test get_network_info tool."""
        mock_instance = MockClient.return_value
        mock_instance.get_network_info.return_value = {"success": True, "network_name": "mainnet"}
        
        result = get_network_info()
        data = json.loads(result)
        self.assertEqual(data["network_name"], "mainnet")

    @patch("chaimcp.main.ChiaRpcClient")
    def test_tool_get_wallet_balance_success(self, MockClient):
        """Test get_wallet_balance tool success."""
        mock_instance = MockClient.return_value
        mock_instance.get_wallet_balance.return_value = {
            "success": True,
            "wallet_balance": {
                "confirmed_wallet_balance": 1500000000000, # 1.5 XCH
                "spendable_balance": 1500000000000
            }
        }
        
        result = get_wallet_balance(1)
        data = json.loads(result)
        # New implementation returns full wallet_balance object
        self.assertEqual(data["wallet_balance"]["confirmed_wallet_balance"], 1500000000000)
        self.assertEqual(data["wallet_balance"]["spendable_balance"], 1500000000000)

    @patch("chaimcp.main.ChiaRpcClient")
    def test_tool_get_wallet_balance_failure(self, MockClient):
        """Test get_wallet_balance tool failure."""
        mock_instance = MockClient.return_value
        mock_instance.get_wallet_balance.return_value = {
            "success": False,
            "error": "Wallet locked"
        }
        
        result = get_wallet_balance(1)
        data = json.loads(result)
        self.assertFalse(data["success"])
        self.assertEqual(data["error"], "Wallet locked")

    @patch("chaimcp.main.mcp")
    @patch.dict(os.environ, {"MCP_TRANSPORT": "stdio"})
    def test_main_stdio(self, mock_mcp):
        """Test main execution with stdio transport."""
        main_module.main()
        mock_mcp.run.assert_called_with(transport="stdio")

    @patch("uvicorn.run")
    @patch("chaimcp.main.mcp")
    @patch.dict(os.environ, {"MCP_TRANSPORT": "sse", "MCP_PORT": "8080"})
    @patch("os.path.exists") 
    def test_main_sse_no_ssl(self, mock_exists, mock_mcp, mock_uvicorn):
        """Test main execution with SSE transport and no SSL."""
        mock_exists.return_value = False # No SSL files
        
        main_module.main()
        
        mock_mcp.sse_app.assert_called_once()
        mock_uvicorn.assert_called_once()
        args, kwargs = mock_uvicorn.call_args
        self.assertEqual(kwargs["port"], 8080)
        self.assertNotIn("ssl_keyfile", kwargs)

    @patch("uvicorn.run")
    @patch("chaimcp.main.mcp")
    @patch.dict(os.environ, {"MCP_TRANSPORT": "http", "SSL_KEY_FILE": "k", "SSL_CERT_FILE": "c"})
    @patch("os.path.exists")
    def test_main_http_ssl(self, mock_exists, mock_mcp, mock_uvicorn):
        """Test main execution with HTTP transport and SSL enabled."""
        mock_exists.return_value = True # SSL files exist
        
        main_module.main()
        
        mock_mcp.streamable_http_app.assert_called_once()
        mock_uvicorn.assert_called_once()
        args, kwargs = mock_uvicorn.call_args
        self.assertEqual(kwargs["ssl_keyfile"], "k")
        self.assertEqual(kwargs["ssl_certfile"], "c")

    @patch("uvicorn.run")
    @patch("chaimcp.main.mcp")
    @patch.dict(os.environ, {"MCP_TRANSPORT": "http", "MCP_PORT": "8000"})
    @patch("os.path.exists")
    def test_main_http_prod_config(self, mock_exists, mock_mcp, mock_uvicorn):
        """Test main execution with production config (HTTP, Port 8000, No SSL)."""
        mock_exists.return_value = False # Simulate no SSL files
        
        main_module.main()
        
        mock_mcp.streamable_http_app.assert_called_once()
        mock_uvicorn.assert_called_once()
        args, kwargs = mock_uvicorn.call_args
        self.assertEqual(kwargs["port"], 8000)
        self.assertNotIn("ssl_keyfile", kwargs)

    def test_auth_token_env(self):
        """Test global auth settings initialization with env var."""
        with patch.dict(os.environ, {"MCP_AUTH_TOKEN": "test-token"}):
            reload(main_module)
            self.assertIsNotNone(main_module.auth_settings)
            self.assertIsNotNone(main_module.token_verifier)
            self.assertEqual(main_module.token_verifier.token, "test-token")

    def test_main_execution(self):
        """Test executing the module as a script (covers __name__ == '__main__')."""
        env = os.environ.copy()
        env["MCP_TRANSPORT"] = "stdio"
        env["PYTHONUNBUFFERED"] = "1" # Ensure output is flushed immediately
        
        try:
            process = subprocess.Popen(
                [sys.executable, "-m", "chaimcp.main"],
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            try:
                # Wait a bit for startup
                output, error = process.communicate(timeout=2) 
            except subprocess.TimeoutExpired:
                process.kill()
                output, error = process.communicate()
            
            # Combine output for checking
            full_output = output + error
            
            if "ChaiMCP module loaded" not in full_output:
                # Debugging aid
                print(f"STDOUT: {output}")
                print(f"STDERR: {error}")
            
            self.assertIn("ChaiMCP module loaded", full_output)
            
        except Exception as e:
            self.fail(f"Subprocess execution failed: {e}")

