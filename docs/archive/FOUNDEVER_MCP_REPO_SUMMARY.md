# Foundever MCP Server - Repository Summary

**Location:** `/home/willard/foundever-mcp-server/`
**Git Repository:** Initialized ✅
**Initial Commit:** `ebc04d2`

## What Was Created

### ✅ Complete Repository Structure

```
foundever-mcp-server/               (868KB)
├── README.md                       # Comprehensive documentation
├── QUICKSTART.md                   # 5-minute setup guide
├── LICENSE                         # MIT License
├── requirements.txt                # Python dependencies
├── .gitignore                      # Git exclusions
│
├── src/                            # Source code (7 files)
│   ├── mcp_server.py              # Main MCP server (122KB)
│   ├── enrichment_engine.py       # Style guide enforcement
│   ├── search.py                  # Qdrant semantic search
│   ├── embedder.py                # E5-Mistral embeddings
│   ├── config.py                  # Configuration & personas (45KB)
│   ├── document_tools.py          # RFP parsing (24KB)
│   └── main.py                    # CLI interface
│
├── scripts/                        # Management scripts (4 files)
│   ├── setup.sh                   # Automated installation
│   ├── foundever_load_model.sh    # Model loader (MCP callable)
│   ├── foundever_model_manager.sh # Interactive model manager
│   └── FOUNDEVER_MODELS_README.md # Model documentation
│
├── config/                         # Configuration files
│   └── claude_desktop_config.json # Claude Desktop MCP config
│
├── models/                         # Model information
│   └── README.md                  # Complete model specs
│
└── docs/                           # Documentation (2 files)
    ├── DOCUMENTATION.md           # Original comprehensive docs
    └── README.md                  # Original readme
```

## Key Components

### 1. MCP Server (33 Tools)
**File:** `src/mcp_server.py` (122KB)

**Tool Categories:**
- Core Search (4): `search_claims`, `search_by_persona`, `enrich_section`, `convert_to_practitioner_voice`
- Style Guide (6): `get_style_guide`, `check_voice`, `build_section`, etc.
- Research (8): `validate_claim`, `check_qdrant_coverage`, `check_content_compliance`, etc.
- No-Fabrication (4): `check_for_fabrication`, `llm_fact_check`, etc.
- RFP Input (8): `parse_rfp_requirements`, `generate_clarifying_questions`, etc.
- FinServ (3): `get_finserv_persona`, `get_threat_context`, `get_finserv_metrics`

### 2. Fine-tuned Models

**Q5_K_M (22GB) - Recommended ✅**
- Location: `/media/willard/New Volume/foundever_model_quantized/`
- Quality: 95-98% of original
- VRAM: ~14GB
- Use: 99% of work

**F16 (62GB) - Original**
- Location: `/media/willard/New Volume/foundever_model/`
- Quality: 100% (reference)
- VRAM: ~35GB
- Use: Final production drafts

### 3. Model Management Scripts

**Interactive Manager:**
```bash
~/foundever-mcp-server/scripts/foundever_model_manager.sh
```
- Visual dashboard
- Load/unload models
- Test models
- Status monitoring

**Auto-Loader (MCP callable):**
```bash
~/foundever-mcp-server/scripts/foundever_load_model.sh foundever-voice-q5
```
- Can be called by MCP server
- Checks if model loaded
- Auto-starts Ollama
- Returns success/failure

### 4. Setup & Installation

**Automated Setup:**
```bash
cd ~/foundever-mcp-server
./scripts/setup.sh
```
- Creates virtual environment
- Installs dependencies
- Checks prerequisites
- Creates systemd service file

**Manual Setup:**
```bash
cd ~/foundever-mcp-server
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Quick Start Commands

### 1. Setup (One-time)
```bash
cd ~/foundever-mcp-server
./scripts/setup.sh
```

### 2. Load Model
```bash
# Interactive (recommended first time)
./scripts/foundever_model_manager.sh

# Or direct load
./scripts/foundever_load_model.sh foundever-voice-q5
```

### 3. Start Server
```bash
source venv/bin/activate
python src/mcp_server.py 8420
```

### 4. Configure Claude
```bash
cp config/claude_desktop_config.json ~/.config/claude/claude_desktop_config.json
# Restart Claude Desktop
```

## Git Repository

**Status:** Initialized with initial commit
**Commit:** `ebc04d2`
**Branch:** master
**Files:** 21 tracked files

**To push to GitHub:**
```bash
cd ~/foundever-mcp-server

# Add remote
git remote add origin https://github.com/yourusername/foundever-mcp-server.git

# Push
git branch -M main
git push -u origin main
```

## Documentation

### Primary Docs
- **README.md** - Main documentation with architecture, tools, setup
- **QUICKSTART.md** - 5-minute getting started guide
- **LICENSE** - MIT License

### Technical Docs
- **docs/DOCUMENTATION.md** - Complete technical reference (19KB)
- **models/README.md** - Model specifications and benchmarks
- **scripts/FOUNDEVER_MODELS_README.md** - Model management guide

### Configuration
- **config/claude_desktop_config.json** - Ready-to-use MCP config
- **requirements.txt** - All Python dependencies
- **.gitignore** - Excludes models, logs, cache, etc.

## Dependencies

### Python Packages (requirements.txt)
- **MCP:** mcp, starlette, uvicorn, sse-starlette
- **AI/ML:** torch, transformers, sentence-transformers
- **Database:** qdrant-client
- **Documents:** python-docx, openpyxl, PyPDF2
- **Dev:** pytest, black, ruff, mypy

### External Services
- **Qdrant** - Vector database (port 6333)
- **Ollama** - Model serving (port 11434)
- **MCP Server** - HTTP/SSE server (port 8420)

## Model Training Info

**Base Model:** Qwen/Qwen2.5-32B-Instruct
**Training Date:** 2026-01-27
**Training Examples:** 3,888
**Dataset:** 4,321 total (372 original + 2,469 database + 1,480 synthetic)
**Method:** LoRA (r=16, alpha=32)
**Epochs:** 3
**Final Loss:** 0.8539 (train), 0.8413 (eval)

## Architecture

```
Claude Desktop (User)
    ↓ HTTP/SSE
MCP Server (:8420) - 33 tools
    ↓
Enrichment Engine - Style enforcement
    ↓
Semantic Search - E5-Mistral-7B (4096-dim)
    ↓
Qdrant (:6333) - 600K+ claims, 135K chunks

Ollama (:11434) - Foundever Voice
```

## Next Steps

1. ✅ Repository created and initialized
2. ✅ All code and scripts copied
3. ✅ Documentation written
4. ✅ Git repository initialized

**To Use:**
1. Run setup: `./scripts/setup.sh`
2. Load model: `./scripts/foundever_model_manager.sh`
3. Start server: `python src/mcp_server.py 8420`
4. Configure Claude Desktop
5. Test with Claude!

**To Deploy:**
- See README.md "Production Setup" section
- Install systemd service: `sudo cp foundever-mcp.service /etc/systemd/system/`
- Configure firewall for port 8420
- Set up Nginx reverse proxy (optional)
- Configure SSL/TLS (optional)

## Additional Resources

**In Repository:**
- README.md - Full documentation
- QUICKSTART.md - Quick setup
- docs/DOCUMENTATION.md - Technical details
- models/README.md - Model specs

**External:**
- Models location: `/media/willard/New Volume/foundever_model*/`
- Running MCP server: Check if PID 591177 is active
- Qdrant data: Check collections at localhost:6333

---

**Repository Ready!** 🎉

All code, documentation, and scripts are centralized in:
**`/home/willard/foundever-mcp-server/`**

To get started: `cd ~/foundever-mcp-server && ./scripts/setup.sh`
