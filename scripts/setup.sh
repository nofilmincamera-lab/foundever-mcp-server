#!/bin/bash
# Foundever MCP Server Setup Script
# Automated installation and configuration

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(dirname "$SCRIPT_DIR")"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}═══════════════════════════════════════════════${NC}"
echo -e "${BLUE}  Foundever MCP Server Setup${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════${NC}"
echo ""

# Check Python version
echo -e "${YELLOW}Checking Python version...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}✗ Python 3 not found${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
REQUIRED_VERSION="3.10"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo -e "${RED}✗ Python $REQUIRED_VERSION+ required (found $PYTHON_VERSION)${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Python $PYTHON_VERSION${NC}"

# Check CUDA
echo ""
echo -e "${YELLOW}Checking CUDA...${NC}"
if command -v nvidia-smi &> /dev/null; then
    nvidia-smi --query-gpu=name --format=csv,noheader | head -1
    echo -e "${GREEN}✓ CUDA available${NC}"
else
    echo -e "${YELLOW}⚠ CUDA not found (CPU mode will be slower)${NC}"
fi

# Create virtual environment
echo ""
echo -e "${YELLOW}Creating virtual environment...${NC}"
cd "$REPO_DIR"

if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo -e "${GREEN}✓ Virtual environment created${NC}"
else
    echo -e "${GREEN}✓ Virtual environment exists${NC}"
fi

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
echo ""
echo -e "${YELLOW}Upgrading pip...${NC}"
pip install --upgrade pip

# Install dependencies
echo ""
echo -e "${YELLOW}Installing dependencies...${NC}"
pip install -r requirements.txt

echo -e "${GREEN}✓ Dependencies installed${NC}"

# Create necessary directories
echo ""
echo -e "${YELLOW}Creating directories...${NC}"
mkdir -p logs
mkdir -p data
mkdir -p config
echo -e "${GREEN}✓ Directories created${NC}"

# Check Qdrant
echo ""
echo -e "${YELLOW}Checking Qdrant...${NC}"
if curl -s http://localhost:6333/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Qdrant is running${NC}"
else
    echo -e "${YELLOW}⚠ Qdrant not running at localhost:6333${NC}"
    echo "  To start Qdrant:"
    echo "  docker run -p 6333:6333 -v \$(pwd)/qdrant_storage:/qdrant/storage qdrant/qdrant"
fi

# Check Ollama
echo ""
echo -e "${YELLOW}Checking Ollama...${NC}"
if command -v ollama &> /dev/null; then
    echo -e "${GREEN}✓ Ollama installed${NC}"
    if pgrep -x "ollama" > /dev/null; then
        echo -e "${GREEN}✓ Ollama is running${NC}"
    else
        echo -e "${YELLOW}⚠ Ollama not running${NC}"
        echo "  To start: ollama serve &"
    fi
else
    echo -e "${YELLOW}⚠ Ollama not installed${NC}"
    echo "  Install: curl -fsSL https://ollama.com/install.sh | sh"
fi

# Create example config
echo ""
echo -e "${YELLOW}Creating configuration files...${NC}"

cat > config/mcp_config.json <<EOF
{
    "port": 8420,
    "host": "0.0.0.0",
    "qdrant": {
        "host": "localhost",
        "port": 6333,
        "collections": {
            "claims": "claims",
            "chunks": "unified_chunks"
        }
    },
    "embedding_model": "intfloat/e5-mistral-7b-instruct",
    "ollama": {
        "host": "http://localhost:11434",
        "model": "foundever-voice-q5:latest"
    }
}
EOF

echo -e "${GREEN}✓ Configuration files created${NC}"

# Create systemd service file (optional)
echo ""
echo -e "${YELLOW}Creating systemd service file...${NC}"

cat > foundever-mcp.service <<EOF
[Unit]
Description=Foundever MCP Server
After=network.target qdrant.service

[Service]
Type=simple
User=$USER
WorkingDirectory=$REPO_DIR
Environment="PATH=$REPO_DIR/venv/bin:/usr/local/bin:/usr/bin"
ExecStart=$REPO_DIR/venv/bin/python $REPO_DIR/src/mcp_server.py 8420
Restart=on-failure
RestartSec=5s

[Install]
WantedBy=multi-user.target
EOF

echo -e "${GREEN}✓ Systemd service file created${NC}"
echo "  To install: sudo cp foundever-mcp.service /etc/systemd/system/"
echo "  Then: sudo systemctl enable foundever-mcp"
echo "  Start: sudo systemctl start foundever-mcp"

# Summary
echo ""
echo -e "${BLUE}═══════════════════════════════════════════════${NC}"
echo -e "${GREEN}Setup Complete!${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════${NC}"
echo ""
echo "Next steps:"
echo ""
echo "1. Load Foundever model:"
echo "   ./scripts/foundever_model_manager.sh"
echo ""
echo "2. Start MCP server:"
echo "   python src/mcp_server.py 8420"
echo ""
echo "3. Configure Claude Desktop:"
echo "   See config/claude_desktop_config.json"
echo ""
echo "4. Optional - Install as service:"
echo "   sudo cp foundever-mcp.service /etc/systemd/system/"
echo "   sudo systemctl enable --now foundever-mcp"
echo ""
