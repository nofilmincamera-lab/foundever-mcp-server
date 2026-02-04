# Foundever MCP Server

> **Enterprise RFP Response Generation System**
> MCP server with fine-tuned AI models for Foundever-style professional proposal writing

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

## Overview

The Foundever MCP (Model Context Protocol) Server is a comprehensive system for generating professional RFP responses using Foundever's established writing standards. It combines semantic search over 600K+ evidence claims with fine-tuned language models to ensure consistent, high-quality proposal content.

### Key Features

- 🤖 **33 Specialized MCP Tools** - From claim search to fabrication detection
- 🔍 **600K+ Evidence Claims** - Qdrant vector database with semantic search
- 🎯 **Fine-tuned Models** - Qwen2.5-32B trained on 3,888 Foundever examples
- 📝 **Style Guide Enforcement** - Automated voice and compliance checking
- 🚫 **No-Fabrication Policies** - LLM-powered fact verification
- 📊 **Persona-Based Search** - Tailored for financial services clients
- 🔐 **Proof-Tier System** - T0 marketing → T3 third-party evidence

## Architecture

```
┌─────────────────────────────────────────────────┐
│  Claude / MCP Client                            │
│  https://mcp.riorock.app/mcp/messages           │
└─────────────────┬───────────────────────────────┘
                  │ HTTP/SSE
┌─────────────────▼───────────────────────────────┐
│  MCP Server (Port 8420)                         │
│  - 33 Tool Endpoints                            │
│  - Request handling & validation                │
└─────────────────┬───────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────┐
│  Enrichment Engine                              │
│  - Style guide enforcement                      │
│  - Voice conversion                             │
│  - Evidence integration                         │
└─────────────────┬───────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────┐
│  Semantic Search (E5-Mistral-7B)                │
│  - Claims: 600K vectors (4096-dim)              │
│  - Chunks: 135K vectors (2048-dim)              │
└─────────────────┬───────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────┐
│  Qdrant Vector Database (Port 6333)             │
│  - claims collection                            │
│  - unified_chunks collection                    │
└─────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────┐
│  Ollama + Foundever Voice Model (Port 11434)    │
│  - foundever-voice-q5:latest (22GB, Q5_K_M)     │
│  - foundever-voice-f16:latest (62GB, F16)       │
└──────────────────────────────────────────────────┘
```

## Quick Start

### Prerequisites

- Python 3.10+
- CUDA-capable GPU (recommended: 16GB+ VRAM)
- Qdrant vector database
- Ollama (for model serving)

### Installation

```bash
# Clone repository
git clone https://github.com/yourusername/foundever-mcp-server.git
cd foundever-mcp-server

# Run setup script
./scripts/setup.sh

# Or manual setup:
pip install -r requirements.txt
```

### Start Server

```bash
# Start MCP server
python src/mcp_server.py 8420

# Or as systemd service
sudo systemctl start foundever-mcp.service
```

### Load Model

```bash
# Load quantized model (recommended)
./scripts/foundever_load_model.sh foundever-voice-q5

# Or use interactive manager
./scripts/foundever_model_manager.sh
```

### Configure Claude Desktop

Add to `~/.config/claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "foundever-style-guide": {
      "url": "http://localhost:8420/mcp/messages"
    },
    "ollama": {
      "command": "npx",
      "args": ["-y", "mcp-ollama"],
      "env": {
        "OLLAMA_HOST": "http://localhost:11434",
        "OLLAMA_MODEL": "foundever-voice-q5:latest"
      }
    }
  }
}
```

## Repository Structure

```
foundever-mcp-server/
├── README.md                    # This file
├── LICENSE                      # MIT License
├── requirements.txt             # Python dependencies
├── .gitignore                   # Git ignore patterns
│
├── src/                         # Source code
│   ├── mcp_server.py           # Main MCP server (33 tools)
│   ├── enrichment_engine.py    # Style guide enrichment
│   ├── search.py               # Qdrant semantic search
│   ├── embedder.py             # E5-Mistral embeddings
│   ├── config.py               # Configuration & personas
│   ├── document_tools.py       # RFP document parsing
│   ├── main.py                 # CLI interface
│   └── __init__.py
│
├── scripts/                     # Management scripts
│   ├── setup.sh                # Initial setup
│   ├── foundever_load_model.sh # Model loader
│   ├── foundever_model_manager.sh # Interactive model manager
│   ├── start_server.sh         # Start MCP server
│   └── FOUNDEVER_MODELS_README.md # Model documentation
│
├── models/                      # Model information
│   ├── README.md               # Model details
│   ├── Modelfile.q5           # Ollama Q5_K_M config
│   └── Modelfile.f16          # Ollama F16 config
│
├── config/                      # Configuration files
│   ├── mcp_config.json         # MCP server config
│   ├── claude_desktop_config.json # Claude Desktop config
│   └── qdrant_config.yaml      # Qdrant settings
│
├── docs/                        # Documentation
│   ├── DOCUMENTATION.md        # Complete technical docs
│   ├── README.md               # Original readme
│   ├── API.md                  # API reference
│   ├── TOOLS.md                # Tool descriptions
│   ├── TRAINING.md             # Model training guide
│   └── DEPLOYMENT.md           # Production deployment
│
└── tests/                       # Test suite
    ├── test_mcp_server.py
    ├── test_enrichment.py
    └── test_search.py
```

## MCP Tools (33 Total)

### Core Search Tools
- `search_claims` - Semantic search across 600K+ claims
- `search_by_persona` - Persona-tailored search (PayTech, Banks, etc.)
- `enrich_section` - Enrich content with evidence
- `convert_to_practitioner_voice` - Marketing → practitioner conversion

### Style Guide Tools
- `get_style_guide` - Complete Foundever style guide
- `get_narrative_templates` - Narrative pattern templates
- `check_voice` - Voice analysis (marketing vs practitioner)
- `build_section` - Generate proposal sections

### Research & Validation
- `get_research_guidelines` ⚠️ **CRITICAL** - Research protocol
- `validate_claim` - Claim validation with confidence levels
- `check_qdrant_coverage` - Check evidence availability
- `check_content_compliance` - Scan for violations

### No-Fabrication Tools
- `get_no_fabrication_policy` - Strict no-fabrication rules
- `generate_iteration_request` - Request missing information
- `check_for_fabrication` - Detect fabricated content
- `llm_fact_check` - LLM-powered final verification

### RFP Input Handling
- `parse_rfp_requirements` - Parse client documents
- `generate_clarifying_questions` - Generate questions
- `map_to_style_guide_structure` - Map to proposal structure
- `track_assumptions` - Track unconfirmed assumptions

### Financial Services
- `get_finserv_persona` - 12 FinServ persona types
- `get_threat_context` - Threat descriptions (APP fraud, etc.)
- `get_finserv_metrics` - Metrics that matter

[See complete tool list in docs/TOOLS.md](docs/TOOLS.md)

## Model Information

### Foundever Voice Model

**Base:** Qwen/Qwen2.5-32B-Instruct
**Training Date:** 2026-01-27
**Training Examples:** 3,888
**Validation Examples:** 433
**Epochs:** 3
**LoRA r/alpha:** 16/32

**Dataset Composition:**
- Original voice patterns: 372
- Enhanced database: 2,469
- Synthetic: 1,480
- **Total:** 4,321

### Available Versions

| Version | Size | Quality | VRAM | Use Case |
|---------|------|---------|------|----------|
| **Q5_K_M** ✅ | 22GB | Very Good | ~14GB | Recommended for most work |
| F16 | 62GB | Highest | ~35GB | Final production drafts |

**Model Locations:**
- F16: `/media/willard/New Volume/foundever_model/`
- Q5_K_M: `/media/willard/New Volume/foundever_model_quantized/`

[See complete model documentation](scripts/FOUNDEVER_MODELS_README.md)

## Configuration

### Environment Variables

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

### Qdrant Collections

Required collections:
- `claims` - 600K+ vectors (4096-dim, E5-Mistral-7B)
- `unified_chunks` - 135K vectors (2048-dim)

## Development

### Running Tests

```bash
# Run all tests
pytest tests/

# Run specific test
pytest tests/test_mcp_server.py

# With coverage
pytest --cov=src tests/
```

### Code Style

```bash
# Format code
black src/

# Lint
ruff check src/

# Type checking
mypy src/
```

## Deployment

### Production Setup

See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) for:
- Systemd service configuration
- Nginx reverse proxy setup
- SSL/TLS configuration
- Monitoring and logging
- Backup strategies

### Public Endpoint

The server can be exposed via Tailscale + Caddy:
- **Local:** http://localhost:8420
- **Tailscale:** http://100.120.219.80:8420
- **Public:** https://mcp.riorock.app

## Documentation

- [Complete Documentation](docs/DOCUMENTATION.md) - Full technical reference
- [API Reference](docs/API.md) - MCP API endpoints
- [Tool Reference](docs/TOOLS.md) - All 33 tools detailed
- [Training Guide](docs/TRAINING.md) - Model training process
- [Model README](scripts/FOUNDEVER_MODELS_README.md) - Model management

## Troubleshooting

### Common Issues

**Ollama not responding:**
```bash
# Check Ollama status
pgrep ollama

# Start Ollama
ollama serve &

# Load model
./scripts/foundever_load_model.sh foundever-voice-q5
```

**MCP server not starting:**
```bash
# Check port availability
lsof -i :8420

# Check logs
tail -f /var/log/foundever-mcp/mcp_server.log
```

**Qdrant connection failed:**
```bash
# Check Qdrant status
curl http://localhost:6333/health

# Start Qdrant
docker start qdrant
```

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## License

MIT License - see [LICENSE](LICENSE) file

## Credits

- **Base Model:** Qwen/Qwen2.5-32B-Instruct (Alibaba Cloud)
- **Embeddings:** intfloat/e5-mistral-7b-instruct
- **Vector DB:** Qdrant
- **Model Serving:** Ollama
- **Framework:** MCP (Model Context Protocol)

## Support

- **Issues:** [GitHub Issues](https://github.com/yourusername/foundever-mcp-server/issues)
- **Documentation:** [docs/](docs/)
- **Model Info:** [scripts/FOUNDEVER_MODELS_README.md](scripts/FOUNDEVER_MODELS_README.md)

---

**Built for Foundever RFP Excellence** 🚀
