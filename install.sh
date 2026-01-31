#!/bin/bash
set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}🍵 ChaiMCP Server Installer${NC}"
echo "=============================="

# Check Python version
if ! command -v python3 &> /dev/null; then
    echo "python3 could not be found. Please install Python 3.10+."
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
REQUIRED_VERSION="3.10"

if (( $(echo "$PYTHON_VERSION < $REQUIRED_VERSION" | bc -l) )); then
    echo -e "${YELLOW}Warning: Python $PYTHON_VERSION detected. Python 3.10+ is recommended.${NC}"
fi

# Create Virtual Environment
echo -e "\n${BLUE}Creating virtual environment...${NC}"
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
    echo "Virtual environment created at .venv"
else
    echo "Virtual environment already exists."
fi

# Install Dependencies
echo -e "\n${BLUE}Installing dependencies...${NC}"
source .venv/bin/activate
pip install --upgrade pip
pip install -e .

echo -e "\n${GREEN}✔ Installation successful!${NC}"
echo "=============================="

# Get absolute path to the executable
VENV_PYTHON=$(pwd)/.venv/bin/python
SCRIPT_PATH=$(pwd)/src/chaimcp/main.py 
# Actually we installed it as a package, so we can run calling the module or the script entry point if installed.
# But since we did `pip install -e .`, `chaimcp` command should be available in venv bin.
EXECUTABLE_PATH=$(pwd)/.venv/bin/chaimcp

echo -e "\n${BLUE}To configure your Agentic IDE (e.g. Claude Desktop):${NC}"

echo -e "\nAdd this to your ${YELLOW}mcp_config.json${NC}:"
echo "{"
echo "  \"mcpServers\": {"
echo "    \"chaimcp\": {"
echo "      \"command\": \"$EXECUTABLE_PATH\","
echo "      \"args\": [],"
echo "      \"disabled\": false,"
echo "      \"autoApprove\": []"
echo "    }"
echo "  }"
echo "}"

echo -e "\n${BLUE}To run manually/debug:${NC}"
echo "$EXECUTABLE_PATH"
