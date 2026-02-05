# CLAUDE.md

## Project Overview

Foundever MCP Server is a Python-based Model Context Protocol (MCP) server that integrates with Claude Desktop for enterprise RFP (Request for Proposal) response generation. It provides 33 specialized tools for semantic search across 600K+ evidence claims, style-guide-enforced proposal writing, LLM-powered fact-checking, and document parsing.

## Repository Structure

```
foundever-mcp-server/
├── src/                          # All Python source code
│   ├── mcp_server.py             # Main MCP server - 33 tool definitions & handlers (3,228 lines)
│   ├── config.py                 # Centralized configuration, data structures, prompt loading
│   ├── search.py                 # Qdrant vector search engine (StyleGuideSearcher)
│   ├── enrichment_engine.py      # Evidence enrichment engine (StyleGuideEnricher)
│   ├── embedder.py               # E5-Mistral-7B embedding singleton (StyleGuideEmbedder)
│   ├── document_tools.py         # RFP document parsing (Word, Excel, PDF)
│   ├── main.py                   # CLI interface for testing (not used by MCP server)
│   └── __init__.py               # Package exports
├── prompts/                      # External prompt files loaded at startup
│   ├── foundever_voice_system.txt  # Foundever Voice model system prompt
│   ├── fact_check_system.txt       # Fact-checking system prompt
│   ├── fact_check_user.txt         # Fact-checking user template ({content}, {evidence})
│   ├── claim_enrichment.txt        # Evidence enrichment prompt
│   ├── proposal_generation.txt     # RFP generation prompt (testing)
│   └── voice_conversion.txt        # Marketing-to-practitioner voice prompt
├── scripts/                      # Setup and model management scripts
│   ├── setup.sh                  # Installation script (Python 3.10+, venv, deps)
│   ├── foundever_load_model.sh   # Load Foundever Voice model into Ollama
│   └── foundever_model_manager.sh  # Interactive model manager
├── config/                       # Runtime configuration
│   └── claude_desktop_config.json  # Claude Desktop MCP server config
├── archive/                      # Archived docs and utilities (not served)
├── ARCHITECTURE.md               # Comprehensive architecture documentation
├── TOOLS_QUICK_REFERENCE.md      # Quick reference for all 33 MCP tools
├── LOADING_BEHAVIOR.md           # Model pre-loading behavior documentation
├── STARTUP_INSTRUCTIONS.md       # Server startup guide
├── requirements.txt              # Python dependencies
└── .gitignore
```

## Tech Stack

- **Language:** Python 3.10+
- **MCP Framework:** `mcp` >= 0.5.0 with `starlette` + `uvicorn` + `sse-starlette`
- **Embeddings:** `intfloat/e5-mistral-7b-instruct` (4096-dim) via `transformers` / `sentence-transformers`
- **Vector DB:** Qdrant (`localhost:6333`) with collections `claims` (600K+) and `unified_chunks` (135K)
- **LLMs:** Ollama (`localhost:11434`) serving `foundever-voice:latest`, `qwen2.5:32b`, `gpt-oss:120b-analytics`
- **Database:** PostgreSQL (`localhost:5432/bpo_enrichment`) for pattern storage
- **Document parsing:** `python-docx`, `openpyxl`, `PyPDF2`
- **HTTP client:** `httpx` (async)

## Architecture

```
Claude Desktop
    ↓ (HTTP/SSE or stdio)
MCP Server (port 8420, src/mcp_server.py)
    ├── Search Engine (src/search.py) → Qdrant
    ├── Enrichment Engine (src/enrichment_engine.py)
    ├── Embedder (src/embedder.py) → E5-Mistral-7B
    ├── Document Tools (src/document_tools.py)
    └── LLM calls → Ollama (foundever-voice, qwen2.5:32b)
```

Models are pre-loaded at startup (`init_models()` in `mcp_server.py:60`) for instant first-call access. Startup takes 10-30 seconds, requiring 7-14 GB for the embedding model.

## Running the Server

```bash
# HTTP/SSE mode (default, port 8420)
python src/mcp_server.py 8420

# Custom port
python src/mcp_server.py 9000

# Stdio mode (Claude Desktop direct)
python src/mcp_server.py --stdio

# Initial setup
bash scripts/setup.sh
```

## Key Source Files

### `src/mcp_server.py` (main server)
- Defines all 33 MCP tools as `Tool()` objects starting at line 115
- Tool handler dispatch at `handle_call_tool()` (line ~1034)
- Pre-loads models via `init_models()` at startup
- All handlers are async; external calls use `httpx`

### `src/config.py` (configuration hub)
- `load_prompt(name)` reads from `prompts/{name}.txt`
- Constants: `CLIENT_PERSONAS` (8 personas), `BUYER_DOMAIN_TAXONOMY` (7 domains), `PROOF_TIERS` (4 tiers), `FINSERV_PERSONAS` (12 personas)
- DB/Qdrant/Ollama connection settings
- Narrative templates, anti-patterns, phrases to use/avoid

### `src/search.py` (vector search)
- `StyleGuideSearcher` class with Qdrant client
- `search_claims()`, `search_chunks()`, `search_for_persona()`, `search_for_style_guide_section()`
- Weighted scoring based on proof tiers (T3 > T2 > T1 > T0)

### `src/embedder.py` (embeddings)
- `StyleGuideEmbedder` singleton pattern
- `embed()`, `embed_batch()`, `embed_for_style_guide()`
- Auto-detects CUDA, falls back to CPU

### `src/enrichment_engine.py` (enrichment)
- `StyleGuideEnricher` with `enrich_section()`, `convert_to_practitioner_voice()`
- Metric extraction, persona framing, taxonomy enrichment

### `src/document_tools.py` (document parsing)
- Parses `.docx`, `.xlsx`, `.pdf` for RFP input
- Auto-saves extracted data to PostgreSQL

## MCP Tools (33 total, 7 categories)

| Category | Tools | Purpose |
|----------|-------|---------|
| Core Search | `search_claims`, `search_by_persona`, `enrich_section`, `convert_to_practitioner_voice` | Evidence discovery |
| Style Guide | `get_style_guide`, `get_narrative_templates`, `check_voice`, `build_section`, `get_response_template`, `search_style_patterns` | Writing standards |
| Research & Validation | `get_research_guidelines`, `validate_claim`, `check_qdrant_coverage`, `format_sourced_content`, `check_content_compliance`, `get_solution_options`, `get_foundever_evidence`, `get_outcome_based_pricing_framing` | Quality assurance |
| No-Fabrication | `get_no_fabrication_policy`, `generate_iteration_request`, `check_for_fabrication`, `llm_fact_check` | Content integrity |
| RFP Input | `parse_rfp_requirements`, `generate_clarifying_questions`, `map_to_style_guide_structure`, `track_assumptions`, document parsing tools | Document processing |
| Financial Services | `get_finserv_persona`, `get_threat_context`, `get_finserv_metrics` | Domain expertise |
| Generation | `generate_rfp_response` | LLM-powered proposal writing |

## Code Conventions

### Python style
- Full type hints on all function signatures
- Async/await for all I/O operations (Qdrant, Ollama, PostgreSQL)
- Dataclasses for structured data (`SearchResult`, `StyleGuideEnrichment`)
- Module-level and function-level docstrings

### Naming
- Classes: `PascalCase` (e.g., `StyleGuideSearcher`, `StyleGuideEmbedder`)
- Functions/methods: `snake_case` (e.g., `search_claims`, `get_embedder`)
- Constants: `UPPER_SNAKE_CASE` (e.g., `QDRANT_HOST`, `EMBEDDING_MODEL`)
- Private methods: `_prefixed` (e.g., `_call_llm`, `_extract_metrics_from_text`)

### Design patterns
- **Singleton:** `StyleGuideEmbedder` ensures one model instance in memory
- **Factory functions:** `get_searcher()`, `get_enricher()`, `get_embedder()`
- **Handler dispatch:** Tool name maps to handler function in `mcp_server.py`
- **External prompts:** System prompts loaded from `prompts/` directory via `load_prompt()`

### Error handling
- Try/except around all external service calls (Ollama, Qdrant, PostgreSQL)
- Graceful fallbacks (CPU if GPU unavailable, warning logs if models not pre-loaded)
- Logging at DEBUG, INFO, WARNING, ERROR levels via `logging` module

## Development Tools

```bash
# Formatting
black src/

# Linting
ruff check src/

# Type checking
mypy src/

# Tests
pytest archive/tests/

# CLI testing (not the MCP server)
python src/main.py --section "collections"
python src/main.py --taxonomy
python src/main.py --convert
```

## External Service Dependencies

The server requires these services running locally:

| Service | Address | Purpose |
|---------|---------|---------|
| Qdrant | `localhost:6333` | Vector database (600K+ claims, 135K chunks) |
| Ollama | `localhost:11434` | LLM inference (foundever-voice, qwen2.5:32b) |
| PostgreSQL | `localhost:5432` | Pattern storage (database: `bpo_enrichment`) |

## Key Domain Concepts

- **Proof Tiers:** T0 (marketing), T1 (vendor artifact), T2 (case study), T3 (third-party recognition). Higher tiers are weighted more heavily in search results.
- **Client Personas:** 8 variable-based templates (paytech, retail_bank, card_issuer, etc.) used instead of real client names.
- **Buyer Domains:** 7 domains (CX Operations, Collections, Financial Crime, Sales, Finance, Trust & Safety, Healthcare).
- **Foundever Voice:** Fine-tuned Qwen2.5-32B model trained on 3,888 RFP examples for practitioner-style writing.
- **No-Fabrication Policy:** Strict rules against unsourced claims, fabricated statistics, unauthorized pricing, and commitment confusion. Use `{{placeholders}}` for unknown data.
- **1-Plus Structure:** Standard proposal section format: framing -> metrics -> point -> capabilities -> differentiators -> value.

## Common Modification Patterns

### Adding a new MCP tool
1. Define the `Tool()` object in `src/mcp_server.py` (add to the `TOOLS` list around line 115)
2. Add the handler function (async, returns `CallToolResult`)
3. Register the handler in the dispatch section of `handle_call_tool()`

### Adding a new prompt
1. Create `prompts/{name}.txt`
2. Load it in `src/config.py` using `load_prompt("name")`
3. Import and use the constant in `src/mcp_server.py`

### Adding a new persona or domain
1. Add the entry to the relevant dict in `src/config.py` (`CLIENT_PERSONAS`, `BUYER_DOMAIN_TAXONOMY`, etc.)
2. Tool input schemas that use `enum` will automatically pick up the new values

### Modifying search behavior
- Search logic is in `src/search.py` (`StyleGuideSearcher`)
- Embedding logic is in `src/embedder.py` (`StyleGuideEmbedder`)
- Proof tier weighting is applied in search result scoring
