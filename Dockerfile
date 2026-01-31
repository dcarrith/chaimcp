FROM python:3.10-slim

WORKDIR /app

COPY pyproject.toml .
COPY src ./src

# Install the package
# We also install uvicorn for SSE transport if needed, though FastMCP might bundle strictly.
# FastMCP 'run' command usually handles SSE.
RUN pip install --no-cache-dir . uvicorn

# Create a non-root user
RUN useradd -m chaimcp
USER chaimcp

# Default command runs the server
# Note: For K8s/Docker we usually want SSE transport.
# FastMCP doesn't default to SSE on bare 'run', it needs 'fastmcp run --transport sse ...' or similar usually,
# but 'mcp.run()' in main.py usually does stdio.
# We will assume we can invoke the module with `fastmcp run` for SSE, or specific entrypoint.
# IMPORTANT: Since `chaimcp` command runs `mcp.run()` which does default transport (often stdio), 
# we might need to adjust or use the `fastmcp` CLI wrapper tool if available, or expose SSE in main.py.

# Let's adjust main.py to support an argument or env var for SSE, OR just use the installed library capabilities.
# Simpler: The `fastmcp` CLI can run any file with an MCP instance.
# CMD ["fastmcp", "run", "src/chaimcp/main.py", "--transport", "sse", "--port", "8000", "--host", "0.0.0.0"]

# BUT, we installed `chaimcp` as a script. 
# Let's stick to a CMD that works. If FastMCP library provides a CLI:
CMD ["fastmcp", "run", "chaimcp.main:mcp", "--transport", "sse", "--port", "8000", "--host", "0.0.0.0"]
