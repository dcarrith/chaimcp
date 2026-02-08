import unittest
from unittest.mock import patch, MagicMock
import os
import sys
from importlib import reload

class TestDisabledTools(unittest.TestCase):

    def setUp(self):
        if 'chaimcp.main' in sys.modules:
            del sys.modules['chaimcp.main']

    @patch("mcp.server.fastmcp.FastMCP.tool")
    @patch.dict(os.environ, {"MCP_DISABLED_TOOLS": "get_blockchain_state, generate_mnemonic"})
    def test_disabled_tools_logic(self, mock_tool):
        """
        Verify that tools listed in MCP_DISABLED_TOOLS are not registered via mcp.tool().
        """
        # We mock mcp.tool to see if it gets called.
        # Note: mcp.tool() returns a decorator, so we have to handle that.
        mock_decorator = MagicMock()
        mock_tool.return_value = mock_decorator
        
        import chaimcp.main
        
        # get_network_info should be registered (NOT disabled)
        # It's defined as @register_tool() -> calls mcp.tool(name=None)
        # So we expect a call to mock_tool(name=None, description=...)
        # We can't easily check 'name' if it's None in the call, but we can check count?
        
        # Let's capture the tool names passed to register_tool which then calls mcp.tool
        # Be careful: My code calls mcp.tool(name=name, description=description).
        # For get_blockchain_state, name is None.
        
        # But since get_blockchain_state IS disabled, mcp.tool SHOULD NOT be called for it.
        # How do we know which call corresponds to which function?
        # The return value of mcp.tool(...) is the decorator, which is called with the function.
        # mock_decorator(func) -> checks func.__name__
        
        registered_funcs = []
        for call in mock_decorator.call_args_list:
            # mock_decorator is called with (func,)
            func = call.args[0]
            registered_funcs.append(func.__name__)
            
        self.assertNotIn("get_blockchain_state", registered_funcs)
        self.assertNotIn("generate_mnemonic", registered_funcs)
        self.assertIn("get_network_info", registered_funcs)

    @patch("mcp.server.fastmcp.FastMCP.tool")
    @patch.dict(os.environ, {"MCP_DISABLED_TOOLS": ""})
    def test_all_tools_enabled(self, mock_tool):
        """Verify all tools registered when config is empty."""
        mock_decorator = MagicMock()
        mock_tool.return_value = mock_decorator
        
        import chaimcp.main
        
        registered_funcs = []
        for call in mock_decorator.call_args_list:
            func = call.args[0]
            registered_funcs.append(func.__name__)
            
        self.assertIn("get_blockchain_state", registered_funcs)
        self.assertIn("generate_mnemonic", registered_funcs)
