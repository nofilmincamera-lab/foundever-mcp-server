# Starting the Foundever MCP Server

## Quick Start

```bash
cd /home/willard/foundever-mcp-server
python src/mcp_server.py 8420
```

**Expected startup time:** 10-30 seconds (models pre-loading)

---

## What Happens at Startup

### Phase 1: Server Initialization (~1 second)
```
✅ Load configuration
✅ Initialize HTTP server
✅ Register MCP tools
```

### Phase 2: Model Pre-Loading (~10-30 seconds)
```
✅ Load E5-Mistral-7B embedder (7-14 GB)
   - Downloads if not cached
   - Loads to GPU if available
   - Falls back to CPU if needed

✅ Connect to Qdrant (50 MB)
   - Connects to localhost:6333
   - Verifies collections exist

✅ Initialize Enricher (10 MB)
   - Loads enrichment engine
   - Links to searcher
```

### Phase 3: Server Ready
```
✅ HTTP server listening on port 8420
✅ All tools ready for instant use
✅ No delays on first tool call
```

---

## Expected Output

### Success
```
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:mcp-style-guide:Starting MCP server on http://0.0.0.0:8420
INFO:mcp-style-guide:MCP endpoint: http://0.0.0.0:8420/mcp/messages
INFO:mcp-style-guide:Health check: http://0.0.0.0:8420/health
INFO:mcp-style-guide:
INFO:mcp-style-guide:Pre-loading models (this may take 10-30 seconds)...
INFO:mcp-style-guide:============================================================
INFO:mcp-style-guide:PRE-LOADING MODELS AT STARTUP
INFO:mcp-style-guide:============================================================
INFO:mcp-style-guide:Loading Searcher + Embedder...
INFO:mcp-style-guide:  → E5-Mistral-7B (7-14 GB, ~10-30s)
INFO:mcp-style-guide:  → Qdrant Client (~50 MB, ~0.5s)
[Embedder] Initializing on cuda
[Embedder] Loading model: intfloat/e5-mistral-7b-instruct
[Embedder] Model loaded. Embedding dim: 4096
[Searcher] Connected to Qdrant at localhost:6333
INFO:mcp-style-guide:✓ Searcher + Embedder loaded successfully
INFO:mcp-style-guide:Loading Enricher...
INFO:mcp-style-guide:  → Enrichment Engine (~10 MB, ~0.1s)
INFO:mcp-style-guide:✓ Enricher loaded successfully
INFO:mcp-style-guide:============================================================
INFO:mcp-style-guide:ALL MODELS PRE-LOADED - SERVER READY
INFO:mcp-style-guide:============================================================
INFO:mcp-style-guide:
INFO:mcp-style-guide:Starting HTTP server...
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8420 (Press CTRL+C to quit)
```

### Health Check
```bash
curl http://localhost:8420/health
```
Response:
```json
{"status": "healthy"}
```

---

## Startup Options

### Default (HTTP Server)
```bash
python src/mcp_server.py 8420
```
- Listens on port 8420
- Accessible via HTTP/SSE
- Pre-loads all models

### Custom Port
```bash
python src/mcp_server.py 9000
```
- Listens on port 9000

### Stdio Mode (Claude Desktop)
```bash
python src/mcp_server.py --stdio
```
- Uses stdio for communication
- Still pre-loads all models
- For local Claude Desktop integration

---

## Troubleshooting

### Slow Startup (>60 seconds)
**Possible causes:**
- Running on CPU (slower than GPU)
- First-time model download
- Limited RAM/VRAM

**Solutions:**
```bash
# Check if GPU available
python -c "import torch; print(f'GPU: {torch.cuda.is_available()}')"

# Check available memory
free -h

# Check model cache location
ls -lh ~/.cache/huggingface/hub/
```

### Qdrant Connection Failed
**Error:** `Failed to connect to Qdrant at localhost:6333`

**Solution:**
```bash
# Check if Qdrant is running
curl http://localhost:6333/health

# Start Qdrant (if using Docker)
docker start qdrant

# Or start Qdrant manually
qdrant --config /path/to/config.yaml
```

### Out of Memory
**Error:** `CUDA out of memory` or `RuntimeError: [enforce fail at alloc_cpu.cpp:...]`

**Solutions:**
1. **Use CPU mode:**
   ```bash
   # Set environment variable
   export CUDA_VISIBLE_DEVICES=""
   python src/mcp_server.py 8420
   ```

2. **Reduce model precision:** (requires code changes)
   - Change `torch_dtype=torch.float16` to `torch.float32` in embedder.py

3. **Increase swap space:**
   ```bash
   # Check current swap
   swapon --show

   # Create swap file if needed
   sudo fallocate -l 16G /swapfile
   sudo mkswap /swapfile
   sudo swapon /swapfile
   ```

### Model Download Fails
**Error:** `Connection timed out` or `Failed to download model`

**Solution:**
```bash
# Pre-download model manually
python -c "
from transformers import AutoTokenizer, AutoModel
model_name = 'intfloat/e5-mistral-7b-instruct'
print('Downloading tokenizer...')
AutoTokenizer.from_pretrained(model_name)
print('Downloading model...')
AutoModel.from_pretrained(model_name)
print('Done!')
"
```

---

## System Requirements

### Minimum
- **Python:** 3.10+
- **RAM:** 16 GB (CPU mode)
- **VRAM:** 16 GB (GPU mode)
- **Disk:** 50 GB (model cache)
- **Qdrant:** Running on localhost:6333

### Recommended
- **Python:** 3.11+
- **RAM:** 32 GB
- **VRAM:** 24 GB (NVIDIA GPU)
- **Disk:** 100 GB SSD
- **Qdrant:** Docker container or systemd service

---

## Running as a Service

### Systemd Service

**Create service file:**
```bash
sudo nano /etc/systemd/system/foundever-mcp.service
```

**Content:**
```ini
[Unit]
Description=Foundever MCP Server
After=network.target qdrant.service

[Service]
Type=simple
User=willard
WorkingDirectory=/home/willard/foundever-mcp-server
ExecStart=/usr/bin/python3 /home/willard/foundever-mcp-server/src/mcp_server.py 8420
Restart=on-failure
RestartSec=10s
StandardOutput=journal
StandardError=journal

# Environment variables
Environment="CUDA_VISIBLE_DEVICES=0"

[Install]
WantedBy=multi-user.target
```

**Enable and start:**
```bash
sudo systemctl daemon-reload
sudo systemctl enable foundever-mcp.service
sudo systemctl start foundever-mcp.service
```

**Check status:**
```bash
sudo systemctl status foundever-mcp.service
```

**View logs:**
```bash
sudo journalctl -u foundever-mcp.service -f
```

---

## Performance Notes

### Startup Time Breakdown
```
Configuration:         0.1s
HTTP Server Init:      0.5s
Model Download:        0-300s (first time only)
Embedder Load:         10-25s (GPU) or 30-60s (CPU)
Qdrant Connection:     0.5s
Enricher Init:         0.1s
─────────────────
Total (first time):    10-30s (cached models)
Total (fresh install): 50-300s (with download)
```

### Memory Usage
```
Python + Dependencies:  ~200 MB
E5-Mistral-7B:          ~7-14 GB (depends on precision)
Qdrant Client:          ~50 MB
Enricher:               ~10 MB
─────────────────
Total:                  ~7-14 GB
```

### Tool Performance (After Startup)
```
Config-based tools:     <10 ms
Search tools:           1-2 seconds
Enrichment tools:       2-5 seconds
LLM tools (Ollama):     5-30 seconds
```

---

## Next Steps After Startup

### 1. Test Health Check
```bash
curl http://localhost:8420/health
```

### 2. Test MCP Endpoint
```bash
curl http://localhost:8420/info
```

### 3. Configure Claude Desktop
Add to `~/.config/claude/claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "foundever-style-guide": {
      "url": "http://localhost:8420/mcp/messages"
    }
  }
}
```

### 4. Test a Tool
Use Claude to test:
```
"Search for collections evidence"
```

Expected: Instant response (models already loaded)

---

**Last Updated:** February 5, 2026
**Status:** Pre-loading enabled by default
