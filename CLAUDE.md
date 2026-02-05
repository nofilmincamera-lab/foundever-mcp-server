# CLAUDE.md

## Project Overview

Foundever MCP Server (v1.1.0) is a Python-based Model Context Protocol (MCP) server that integrates with Claude Desktop for enterprise RFP (Request for Proposal) response generation. It serves **50 specialized tools** (35 core + 15 document tools) for semantic search across 600K+ evidence claims, style-guide-enforced proposal writing, LLM-powered fact-checking, and document parsing across PDF, Excel, Word, and PowerPoint formats.

## Repository Structure

```
foundever-mcp-server/
├── src/                            # All Python source code (6,379 lines total)
│   ├── mcp_server.py               # Main MCP server - 35 tool definitions & handlers (3,282 lines)
│   ├── config.py                   # Centralized configuration, data structures, prompt loading (810 lines)
│   ├── search.py                   # Qdrant vector search engine (531 lines)
│   ├── enrichment_engine.py        # Evidence enrichment engine (513 lines)
│   ├── embedder.py                 # E5-Mistral-7B embedding singleton (135 lines)
│   ├── document_tools.py           # Document parsing - PDF, Excel, Word, PPTX (682 lines)
│   ├── main.py                     # CLI interface for testing (394 lines)
│   └── __init__.py                 # Package exports (32 lines)
├── prompts/                        # External prompt files loaded at startup
│   ├── foundever_voice_system.txt  # Foundever Voice model system prompt
│   ├── fact_check_system.txt       # Fact-checking system prompt
│   ├── fact_check_user.txt         # Fact-checking user template ({content}, {evidence})
│   ├── claim_enrichment.txt        # Evidence enrichment prompt
│   ├── proposal_generation.txt     # RFP generation prompt
│   └── README.md                   # Prompt documentation
├── scripts/                        # Setup and model management scripts
│   ├── setup.sh                    # Installation script (Python 3.10+, venv, deps)
│   ├── foundever_load_model.sh     # Load Foundever Voice model into Ollama
│   ├── foundever_model_manager.sh  # Interactive model manager
│   └── FOUNDEVER_MODELS_README.md  # Model documentation
├── config/                         # Runtime configuration
│   └── claude_desktop_config.json  # Claude Desktop MCP server config
├── Docs/                           # Generated analysis data
│   ├── classification_report.json  # Classification metrics (1.2 MB)
│   ├── domain_specific_classification.json  # Domain classifications (1.7 MB)
│   └── slide_library_index.json    # Presentation library index (3.2 MB)
├── archive/                        # Archived docs and utilities (not served)
│   ├── docs/                       # Historical documentation
│   ├── models/                     # Model documentation
│   └── utils/                      # Utility scripts (e.g., foundever_voice_reviewer.py)
├── README.md                       # Project overview and quick start
├── ARCHITECTURE.md                 # Comprehensive architecture documentation (1,215 lines)
├── TOOLS_QUICK_REFERENCE.md        # Quick reference for all MCP tools
├── LOADING_BEHAVIOR.md             # Model pre-loading behavior documentation
├── STARTUP_INSTRUCTIONS.md         # Server startup guide
├── LICENSE                         # MIT License
├── requirements.txt                # Python dependencies
└── .gitignore
```

## Tech Stack

- **Language:** Python 3.10+
- **MCP Framework:** `mcp` >= 0.5.0 with `starlette` + `uvicorn` + `sse-starlette`
- **Embeddings:** `intfloat/e5-mistral-7b-instruct` (4096-dim) via `transformers` / `sentence-transformers`
- **Vector DB:** Qdrant (`localhost:6333`) with collections:
  - `claims` — 600K+ vectors, 4096-dim (evidence claims)
  - `unified_chunks` — 135K vectors, 2048-dim (document chunks)
- **LLMs:** Ollama (`localhost:11434`) serving:
  - `foundever-voice:latest` — Fine-tuned Qwen2.5-32B for RFP voice (4,321 training examples)
  - `qwen2.5:32b` — Fact-checking model (20 GB)
  - `gpt-oss:120b-analytics` — Complex analysis tasks (65 GB)
- **Database:** PostgreSQL (`localhost:5432/bpo_enrichment`) for pattern storage
- **Document parsing:** `python-docx`, `openpyxl`, `PyPDF2` (+ pandoc and markitdown for DOCX/PPTX conversion)
- **HTTP client:** `httpx` (async)

## Architecture

```
Claude Desktop
    ↓ (HTTP/SSE or stdio)
MCP Server (port 8420, src/mcp_server.py)
    ├── Search Engine (src/search.py) → Qdrant (claims + unified_chunks)
    ├── Enrichment Engine (src/enrichment_engine.py) → Ollama LLMs
    ├── Embedder (src/embedder.py) → E5-Mistral-7B (GPU/CPU)
    ├── Document Tools (src/document_tools.py) → PDF, XLSX, DOCX, PPTX
    └── LLM calls → Ollama (foundever-voice, qwen2.5:32b, gpt-oss:120b)
```

**HTTP endpoints:**
- `GET /mcp` — SSE connection for MCP clients
- `POST /mcp/messages` — MCP message handling
- `GET /health` — Health check with tool/persona/domain counts
- `GET /info` — Server metadata and tool listing
- `POST /tools/{tool_name}` — Direct REST tool invocation (convenience)

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

### `src/mcp_server.py` (3,282 lines — main server)
- Defines 35 core MCP tools as `Tool()` objects starting at line 115
- Also serves 15 document tools imported from `document_tools.py` (50 tools total)
- Tool handler dispatch at `handle_tool_call()` (line 1070) — tries document tools first, then core tools
- Pre-loads models via `init_models()` at startup (line 60)
- MCP server registered as `"style-guide-enrichment"` (line 3160)
- All handlers are async; external calls use `httpx` and `psycopg2`

### `src/config.py` (810 lines — configuration hub)
- `load_prompt(name)` reads from `prompts/{name}.txt`
- Constants: `CLIENT_PERSONAS` (8 personas), `BUYER_DOMAIN_TAXONOMY` (7 domains), `PROOF_TIERS` (4 tiers), `FINSERV_PERSONAS` (12 personas)
- DB/Qdrant/Ollama connection settings
- Narrative templates (`NARRATIVE_TEMPLATES`), anti-patterns (`ANTI_PATTERNS`), phrases to use/avoid
- Voice conversion pairs (`VOICE_CONVERSIONS`), persona value statements (`PERSONA_VALUE_STATEMENTS`)
- Threat contexts (`THREAT_CONTEXTS`) with 4 financial crime scenarios
- Research guidelines (`RESEARCH_GUIDELINES`), 1-Plus structure (`ONE_PLUS_STRUCTURE`)
- FinServ metrics (`FINSERV_METRICS`) across 7 categories
- Section template (`SECTION_TEMPLATE`) for structured output

### `src/search.py` (531 lines — vector search)
- `StyleGuideSearcher` class with Qdrant client
- `SearchResult` dataclass with `weighted_score` property applying proof tier weights
- `search_claims()` — searches `claims` collection (600K, 4096-dim)
- `search_chunks()` — searches `unified_chunks` collection (135K, 2048-dim) with scroll fallback
- `search_for_persona()` — enriches query with persona keywords, searches per domain
- `search_for_style_guide_section()` — comprehensive section enrichment (high_quality, case_study, outcomes, capabilities)
- `get_provider_evidence()` — full evidence package for a provider, categorized by tier/domain/type

### `src/embedder.py` (135 lines — embeddings)
- `StyleGuideEmbedder` singleton pattern (one model instance in memory)
- `embed()` — single text embedding (4096-dim output)
- `embed_batch()` — batch embeddings with `"query: "` prefix for e5-mistral
- `embed_for_style_guide()` — optimized embedding with domain/context enrichment
- Auto-detects CUDA (float16) or falls back to CPU (float32), max 512 tokens

### `src/enrichment_engine.py` (513 lines — enrichment)
- `StyleGuideEnricher` class with optional LLM integration (`use_llm=True`)
- Dataclasses: `EnrichedExample`, `TaxonomyEnrichment`, `StyleGuideEnrichment`
- `enrich_section()` — main entry point: enriches a topic with persona examples, taxonomy, and Foundever patterns
- `generate_practitioner_examples()` — converts marketing phrases to practitioner voice
- `enrich_taxonomy()` — enriches all 7 buyer domains with evidence
- `_extract_metrics_from_text()` — regex extraction of percentages, dollars, time values, ratios
- `_identify_foundever_patterns()` — extracts voice characteristics, metrics, differentiators

### `src/document_tools.py` (682 lines — document parsing)
- 15 document tool definitions (PDF: 5, Excel: 4, Word: 3, PowerPoint: 3)
- `handle_document_tool()` — async dispatch for all document tools
- `save_to_training_db()` — auto-saves extracted content to PostgreSQL `document_training_data` table
- PDF: extract text, extract tables, merge, split, metadata
- Excel: read (JSON), analyze (statistics), write, convert to CSV
- Word: extract text+tables, convert to markdown (via pandoc), metadata
- PowerPoint: extract text by slide, convert to markdown (via markitdown), metadata

### `src/main.py` (394 lines — CLI testing)
- CLI interface for testing enrichment functions (not used by MCP server)
- `--section` for section enrichment, `--taxonomy` for domain enrichment, `--convert` for voice conversion
- `--json` flag for JSON output format

### `src/__init__.py` (32 lines — package exports)
- Exports: `CLIENT_PERSONAS`, `BUYER_DOMAIN_TAXONOMY`, `PROOF_TIERS`
- Exports: `StyleGuideEmbedder`, `StyleGuideSearcher`, `StyleGuideEnricher` and their factory functions
- Exports: dataclasses `SearchResult`, `StyleGuideEnrichment`, `TaxonomyEnrichment`, `EnrichedExample`

## MCP Tools (50 total: 35 core + 15 document)

### Core Tools (35 in `src/mcp_server.py`)

| Category | Tools | Purpose |
|----------|-------|---------|
| Core Search (4) | `search_claims`, `search_by_persona`, `enrich_section`, `convert_to_practitioner_voice` | Evidence discovery and enrichment |
| Evidence (1) | `get_foundever_evidence` | Comprehensive evidence package for a provider |
| Reference Data (3) | `get_taxonomy`, `get_personas`, `get_phrases` | Buyer domains, client personas, phrase guidance |
| Style Guide (6) | `get_style_guide`, `get_narrative_templates`, `check_voice`, `build_section`, `get_response_template`, `search_style_patterns` | Writing standards and templates |
| Financial Services (4) | `get_finserv_persona`, `get_threat_context`, `get_finserv_metrics`, `get_anti_patterns` | FinServ domain expertise |
| Research & Validation (7) | `get_research_guidelines`, `validate_claim`, `check_qdrant_coverage`, `format_sourced_content`, `check_content_compliance`, `get_solution_options`, `get_outcome_based_pricing_framing` | Quality assurance |
| No-Fabrication (4) | `get_no_fabrication_policy`, `generate_iteration_request`, `check_for_fabrication`, `llm_fact_check` | Content integrity enforcement |
| RFP Input (5) | `parse_rfp_requirements`, `generate_clarifying_questions`, `map_to_style_guide_structure`, `track_assumptions`, `enrich_taxonomy` | Document processing and mapping |
| Generation (1) | `generate_rfp_response` | Fine-tuned voice model proposal writing |

### Document Tools (15 in `src/document_tools.py`)

| Format | Tools | Operations |
|--------|-------|------------|
| PDF (5) | `pdf_extract_text`, `pdf_extract_tables`, `pdf_merge`, `pdf_split`, `pdf_metadata` | Read, extract, merge, split |
| Excel (4) | `xlsx_read`, `xlsx_analyze`, `xlsx_write`, `xlsx_to_csv` | Read, analyze, write, convert |
| Word (3) | `docx_extract_text`, `docx_to_markdown`, `docx_metadata` | Extract, convert, metadata |
| PowerPoint (3) | `pptx_extract_text`, `pptx_to_markdown`, `pptx_metadata` | Extract, convert, metadata |

## Code Conventions

### Python style
- Full type hints on all function signatures
- Async/await for all I/O operations (Qdrant, Ollama, PostgreSQL)
- Dataclasses for structured data (`SearchResult`, `StyleGuideEnrichment`, `EnrichedExample`, `TaxonomyEnrichment`)
- Module-level and function-level docstrings

### Naming
- Classes: `PascalCase` (e.g., `StyleGuideSearcher`, `StyleGuideEmbedder`)
- Functions/methods: `snake_case` (e.g., `search_claims`, `get_embedder`)
- Constants: `UPPER_SNAKE_CASE` (e.g., `QDRANT_HOST`, `EMBEDDING_MODEL`)
- Private methods: `_prefixed` (e.g., `_call_llm`, `_extract_metrics_from_text`)

### Design patterns
- **Singleton:** `StyleGuideEmbedder` ensures one model instance in memory
- **Factory functions:** `get_searcher()`, `get_enricher()`, `get_embedder()`
- **Handler dispatch:** `handle_tool_call()` tries document tools first, then core tool dispatch
- **External prompts:** System prompts loaded from `prompts/` directory via `load_prompt()`
- **Lazy loading with pre-load:** Models pre-loaded at startup; `get_lazy_searcher()`/`get_lazy_enricher()` provide fallback initialization

### Error handling
- Try/except around all external service calls (Ollama, Qdrant, PostgreSQL)
- Graceful fallbacks (CPU if GPU unavailable, warning logs if models not pre-loaded)
- Logging at DEBUG, INFO, WARNING, ERROR levels via `logging` module
- Document tools return `None` for unmatched names, allowing fallthrough to core handlers

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
| Qdrant | `localhost:6333` | Vector database (600K+ claims at 4096-dim, 135K chunks at 2048-dim) |
| Ollama | `localhost:11434` | LLM inference (foundever-voice, qwen2.5:32b, gpt-oss:120b-analytics) |
| PostgreSQL | `localhost:5432` | Pattern storage and training data (database: `bpo_enrichment`, user: `bpo_user`) |

## Key Domain Concepts

- **Proof Tiers:** T0 (marketing, weight 0.3), T1 (vendor artifact, weight 0.7), T2 (case study, weight 0.85), T3 (third-party recognition, weight 1.0). Higher tiers are weighted more heavily in search results.
- **Client Personas:** 8 base templates (paytech, retail_bank, card_issuer, investment_bank, insurance_carrier, mortgage_servicer, fintech_lender, collections_agency) + 12 FinServ personas. Used instead of real client names.
- **Buyer Domains:** 7 domains — CX Operations, Collections & Revenue Recovery, Financial Crime & Compliance, Sales Operations, Finance & Accounting, Trust & Safety, Tech Support.
- **Foundever Voice:** Fine-tuned Qwen2.5-32B model trained on 4,321 RFP examples for practitioner-style writing.
- **No-Fabrication Policy:** Strict rules against unsourced claims, fabricated statistics, unauthorized pricing, and commitment confusion. Use `{{placeholders}}` for unknown data.
- **1-Plus Structure:** Standard proposal section format: framing -> metrics -> point -> what you asked for -> what you get -> value.
- **Threat Contexts:** 4 financial crime scenarios (APP Fraud, Reg E Dispute Surge, CFPB Enforcement, Deepfakes & Synthetic Identity).
- **Voice Conversions:** 12 marketing-to-practitioner pairs + 8 AI-to-human pairs for consistent voice tone.

## Common Modification Patterns

### Adding a new MCP tool
1. Define the `Tool()` object in `src/mcp_server.py` (add to the `TOOLS` list starting at line 115)
2. Add the handler logic in `handle_tool_call()` (line 1070) as a new `elif name == "your_tool"` branch
3. The tool is automatically served — `list_tools()` (line 3163) returns `TOOLS + DOCUMENT_TOOLS`

### Adding a new document tool
1. Add the `Tool()` definition to the `DOCUMENT_TOOLS` list in `src/document_tools.py` (line 457)
2. Add the handler in `handle_document_tool()` function
3. It is automatically included via the import in `mcp_server.py` line 45

### Adding a new prompt
1. Create `prompts/{name}.txt`
2. Load it in `src/config.py` using `load_prompt("name")`
3. Import and use the constant in `src/mcp_server.py`

### Adding a new persona or domain
1. Add the entry to the relevant dict in `src/config.py` (`CLIENT_PERSONAS`, `BUYER_DOMAIN_TAXONOMY`, `FINSERV_PERSONAS`, etc.)
2. Tool input schemas that use `enum` will automatically pick up the new values

### Modifying search behavior
- Search logic is in `src/search.py` (`StyleGuideSearcher`)
- Embedding logic is in `src/embedder.py` (`StyleGuideEmbedder`)
- Proof tier weights are defined in `PROOF_TIERS` in `src/config.py`
- Default search limit: 20 (`DEFAULT_SEARCH_LIMIT`), minimum similarity: 0.65 (`MIN_SIMILARITY_SCORE`)

### Modifying LLM behavior
- LLM models are configured in `src/config.py` (lines 63-66): `OLLAMA_URL`, `LLM_MODEL`, `FACT_CHECK_MODEL`, `FOUNDEVER_VOICE_MODEL`
- System prompts are in the `prompts/` directory; edit the `.txt` files directly
- LLM calls go through `httpx` to Ollama's `/api/generate` endpoint
