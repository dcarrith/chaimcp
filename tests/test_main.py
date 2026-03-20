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
    def setUp(self):
        self.config_patcher = patch("chaimcp.chia_client.load_chia_config", return_value={"selected_network": "mainnet", "full_node": {"port": 8555}, "wallet": {"port": 9256}})
        self.mock_config = self.config_patcher.start()
        
    def tearDown(self):
        self.config_patcher.stop()

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

    @patch("chaimcp.chia_client.ChiaRpcClient.get_blockchain_state")
    def test_tool_get_blockchain_state_success(self, mock_get):
        """Test get_blockchain_state tool success path."""
        mock_get.return_value = {
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

    @patch("chaimcp.chia_client.ChiaRpcClient.get_blockchain_state")
    def test_tool_get_blockchain_state_failure(self, mock_get):
        """Test get_blockchain_state tool failure path."""
        mock_get.return_value = {
            "success": False,
            "error": "RPC Error"
        }
        
        result = get_blockchain_state()
        data = json.loads(result)
        self.assertFalse(data["success"])
        self.assertEqual(data["error"], "RPC Error")

    @patch("chaimcp.chia_client.ChiaRpcClient.get_network_info")
    def test_tool_get_network_info(self, mock_get):
        """Test get_network_info tool."""
        mock_get.return_value = {"success": True, "network_name": "mainnet"}
        
        result = get_network_info()
        data = json.loads(result)
        self.assertEqual(data["network_name"], "mainnet")

    @patch("chaimcp.chia_client.ChiaRpcClient.get_wallet_balance")
    def test_tool_get_wallet_balance_success(self, mock_get):
        """Test get_wallet_balance tool success."""
        mock_get.return_value = {
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

    @patch("chaimcp.chia_client.ChiaRpcClient.get_wallet_balance")
    def test_tool_get_wallet_balance_failure(self, mock_get):
        """Test get_wallet_balance tool failure."""
        mock_get.return_value = {
            "success": False,
            "error": "Wallet locked"
        }
        
        result = get_wallet_balance(1)
        data = json.loads(result)
        self.assertFalse(data["success"])
        self.assertEqual(data["error"], "Wallet locked")

    @patch("mcp.server.fastmcp.FastMCP.run")
    @patch.dict(os.environ, {"MCP_TRANSPORT": "stdio"})
    def test_main_stdio(self, mock_run):
        """Test main execution with stdio transport."""
        main_module.main()
        mock_run.assert_called_with(transport="stdio")

    @patch("uvicorn.run")
    @patch("mcp.server.fastmcp.FastMCP.sse_app")
    @patch.dict(os.environ, {"MCP_TRANSPORT": "sse", "MCP_PORT": "8080"})
    @patch("os.path.exists") 
    def test_main_sse_no_ssl(self, mock_exists, mock_sse, mock_uvicorn):
        """Test main execution with SSE transport and no SSL."""
        mock_exists.return_value = False # No SSL files
        mock_sse.return_value.routes = []
        main_module.main()
        
        mock_sse.assert_called_once()
        mock_uvicorn.assert_called_once()
        args, kwargs = mock_uvicorn.call_args
        self.assertEqual(kwargs["port"], 8080)
        self.assertNotIn("ssl_keyfile", kwargs)

    @patch("uvicorn.run")
    @patch("mcp.server.fastmcp.FastMCP.streamable_http_app")
    @patch.dict(os.environ, {"MCP_TRANSPORT": "http", "SSL_KEY_FILE": "k", "SSL_CERT_FILE": "c"})
    @patch("os.path.exists")
    def test_main_http_ssl(self, mock_exists, mock_http, mock_uvicorn):
        """Test main execution with HTTP transport and SSL enabled."""
        mock_exists.return_value = True # SSL files exist
        mock_http.return_value.routes = []
        main_module.main()
        
        mock_http.assert_called_once()
        mock_uvicorn.assert_called_once()
        args, kwargs = mock_uvicorn.call_args
        self.assertEqual(kwargs["ssl_keyfile"], "k")
        self.assertEqual(kwargs["ssl_certfile"], "c")

    @patch("uvicorn.run")
    @patch("mcp.server.fastmcp.FastMCP.streamable_http_app")
    @patch.dict(os.environ, {"MCP_TRANSPORT": "http", "MCP_PORT": "8000"})
    @patch("os.path.exists")
    def test_main_http_prod_config(self, mock_exists, mock_http, mock_uvicorn):
        """Test main execution with production config (HTTP, Port 8000, No SSL)."""
        mock_exists.return_value = False # Simulate no SSL files
        mock_http.return_value.routes = []
        main_module.main()
        
        mock_http.assert_called_once()
        mock_uvicorn.assert_called_once()
        args, kwargs = mock_uvicorn.call_args
        self.assertEqual(kwargs["port"], 8000)
        self.assertNotIn("ssl_keyfile", kwargs)


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

