# Foundever MCP Server - Quick Start Guide

Get up and running in 5 minutes!

## Prerequisites Check

```bash
# Check Python version (needs 3.10+)
python3 --version

# Check if you have a GPU (optional but recommended)
nvidia-smi

# Check if Ollama is installed
which ollama

# Check if Qdrant is running
curl http://localhost:6333/health
```

## Installation

```bash
# 1. Navigate to repository
cd ~/foundever-mcp-server

# 2. Run setup script
./scripts/setup.sh

# This will:
# - Create virtual environment
# - Install dependencies
# - Create config files
# - Check prerequisites
```

## Load the Model

```bash
# Option 1: Interactive manager (recommended for first time)
./scripts/foundever_model_manager.sh

# Option 2: Direct load (Q5_K_M - recommended)
./scripts/foundever_load_model.sh foundever-voice-q5

# Option 3: Load F16 (if you have 35GB+ VRAM)
./scripts/foundever_model_manager.sh load-f16
```

## Start the Server

```bash
# Activate virtual environment
source venv/bin/activate

# Start MCP server
python src/mcp_server.py 8420

# Server will be available at:
# - http://localhost:8420
# - http://localhost:8420/mcp/messages (MCP endpoint)
```

## Configure Claude Desktop

```bash
# Copy configuration
cp config/claude_desktop_config.json ~/.config/claude/claude_desktop_config.json

# Or manually add to your existing config
# See config/claude_desktop_config.json for the JSON
```

Restart Claude Desktop after updating the config.

## Test It

### Test 1: Check Server Health

```bash
curl http://localhost:8420/health
# Should return: {"status": "healthy"}
```

### Test 2: Use a Tool

```bash
curl -X POST http://localhost:8420/mcp/tools/get_style_guide \
  -H "Content-Type: application/json" \
  -d '{"section": "voice"}'
```

### Test 3: Test Model

```bash
ollama run foundever-voice-q5:latest "Write a brief acknowledgment of a client requirement for 24/7 support coverage."
```

### Test 4: Use in Claude Desktop

1. Open Claude Desktop
2. Start a new conversation
3. Try: "Search for claims about fraud detection in financial services"
4. The MCP tools will be automatically available!

## Common Issues

### Issue: "Ollama not responding"

```bash
# Start Ollama
ollama serve &

# Wait a few seconds, then load model
sleep 3
./scripts/foundever_load_model.sh foundever-voice-q5
```

### Issue: "Qdrant connection failed"

```bash
# Start Qdrant with Docker
docker run -d -p 6333:6333 \
  -v $(pwd)/qdrant_storage:/qdrant/storage \
  --name qdrant \
  qdrant/qdrant

# Or if already exists
docker start qdrant
```

### Issue: "Import errors"

```bash
# Make sure virtual environment is activated
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

### Issue: "Model not loading"

```bash
# Check model files exist
ls -lh "/media/willard/New Volume/foundever_model_quantized/"

# Try interactive manager for diagnostics
./scripts/foundever_model_manager.sh
```

## Production Setup

### Run as Systemd Service

```bash
# Copy service file
sudo cp foundever-mcp.service /etc/systemd/system/

# Enable and start
sudo systemctl enable foundever-mcp
sudo systemctl start foundever-mcp

# Check status
sudo systemctl status foundever-mcp

# View logs
sudo journalctl -u foundever-mcp -f
```

### Environment Variables

Create `.env` file:

```bash
# Qdrant
QDRANT_HOST=localhost
QDRANT_PORT=6333

# Ollama
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=foundever-voice-q5:latest

# MCP Server
MCP_PORT=8420
MCP_HOST=0.0.0.0
```

## Next Steps

- Read [docs/DOCUMENTATION.md](docs/DOCUMENTATION.md) for complete reference
- Check [scripts/FOUNDEVER_MODELS_README.md](scripts/FOUNDEVER_MODELS_README.md) for model details
- See [README.md](README.md) for tool descriptions
- Review [models/README.md](models/README.md) for model specs

## Getting Help

- Check logs: `tail -f logs/mcp_server.log`
- Model issues: `./scripts/foundever_model_manager.sh`
- Server issues: `curl http://localhost:8420/health`
- Qdrant issues: `curl http://localhost:6333/health`

## Architecture at a Glance

```
Claude Desktop
    ↓
MCP Server (port 8420) → 33 tools available
    ↓
Enrichment Engine → Style guide enforcement
    ↓
Semantic Search → E5-Mistral-7B embeddings
    ↓
Qdrant (port 6333) → 600K+ claims

Ollama (port 11434) → Foundever Voice model
```

## What You Can Do

With the MCP server running, you can:

✅ Search 600K+ evidence claims semantically
✅ Convert marketing speak to practitioner voice
✅ Validate claims with confidence levels
✅ Check content for fabrications
✅ Get Foundever style guide sections
✅ Generate proposal sections
✅ Parse RFP requirements
✅ Get persona-specific recommendations
✅ Track assumptions
✅ Much more! (33 tools total)

---

**Ready to go!** 🚀

Try asking Claude: *"Search for claims about collections performance metrics in the financial services domain"*
