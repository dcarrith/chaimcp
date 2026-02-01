from mcp.server.fastmcp import FastMCP
import inspect

# Create dummy app to check routes
mcp = FastMCP("test")
app = mcp.streamable_http_app()
print(f"Routes: {app.routes}")
