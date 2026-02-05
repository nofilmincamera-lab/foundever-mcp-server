# CLAUDE.md

## Project Overview

Foundever MCP Server is a Python-based Model Context Protocol (MCP) server that integrates with Claude Desktop for enterprise RFP (Request for Proposal) response generation. It provides 41+ specialized tools for semantic search across 600K+ evidence claims, style-guide-enforced proposal writing, LLM-powered fact-checking, document parsing, slide library management, and PPTX proposal deck generation.

## Repository Structure

```
foundever-mcp-server/
├── src/                          # Python MCP server (backend)
│   ├── mcp_server.py             # Main MCP server - 41+ tool definitions & handlers
│   ├── config.py                 # Centralized configuration, data structures, prompt loading
│   ├── search.py                 # Qdrant vector search engine (StyleGuideSearcher)
│   ├── enrichment_engine.py      # Evidence enrichment engine (StyleGuideEnricher)
│   ├── embedder.py               # E5-Mistral-7B embedding singleton (StyleGuideEmbedder)
│   ├── document_tools.py         # RFP document parsing (Word, Excel, PDF, PPTX)
│   ├── slide_library.py          # Slide library indexing, search, classification
│   ├── pptx_builder.py           # PPTX generation engine (template analysis, deck assembly)
│   ├── pptx_tools.py             # MCP tool definitions for slide library & PPTX builder
│   ├── main.py                   # CLI interface for testing (not used by MCP server)
│   └── __init__.py               # Package exports
├── frontend/                     # Next.js proposal engine (frontend)
│   ├── src/
│   │   ├── app/                  # Next.js App Router pages
│   │   │   ├── layout.tsx        # Root layout with navigation
│   │   │   ├── page.tsx          # Dashboard: projects, sections, taxonomy
│   │   │   ├── intake/page.tsx   # Document upload and classification UI
│   │   │   └── export/page.tsx   # PPTX export: library browse, deck assembly
│   │   ├── lib/
│   │   │   ├── classification/   # 3-layer document classification model
│   │   │   │   ├── types.ts      # TypeScript types for all 3 layers
│   │   │   │   ├── taxonomy.ts   # Canonical labels from 1,000-slide corpus
│   │   │   │   ├── mapping.ts    # FE labels → backend 9-section mapping
│   │   │   │   ├── classifier.ts # Keyword + LLM classification engine
│   │   │   │   └── index.ts      # Public API
│   │   │   ├── document-skills/  # Document intake pipeline
│   │   │   │   ├── intake.ts     # Upload → extract → classify → map flow
│   │   │   │   └── index.ts
│   │   │   ├── mcp/              # MCP server HTTP client
│   │   │   │   └── client.ts     # REST client for 41+ backend tools
│   │   │   └── langbase/         # Langbase orchestration client
│   │   │       └── client.ts     # Pipes (agents) + Memory (RAG) client
│   │   ├── components/           # React components (TBD)
│   │   └── types/                # Shared types (TBD)
│   ├── package.json
│   ├── tsconfig.json
│   └── next.config.ts            # Proxies /api/mcp/* → localhost:8420
├── prompts/                      # External prompt files loaded at startup
│   ├── foundever_voice_system.txt
│   ├── fact_check_system.txt
│   ├── fact_check_user.txt
│   ├── claim_enrichment.txt
│   ├── proposal_generation.txt
│   └── voice_conversion.txt
├── scripts/                      # Setup and model management scripts
├── config/                       # Runtime configuration
├── archive/                      # Archived docs and utilities
├── requirements.txt              # Python dependencies
└── .gitignore
```

## Tech Stack

### Backend (Python MCP Server)
- **Language:** Python 3.10+
- **MCP Framework:** `mcp` >= 0.5.0 with `starlette` + `uvicorn` + `sse-starlette`
- **Embeddings:** `intfloat/e5-mistral-7b-instruct` (4096-dim) via `transformers` / `sentence-transformers`
- **Vector DB:** Qdrant (`localhost:6333`) with collections `claims` (600K+) and `unified_chunks` (135K)
- **LLMs:** Ollama (`localhost:11434`) serving `foundever-voice:latest`, `qwen2.5:32b`, `gpt-oss:120b-analytics`
- **Database:** PostgreSQL (`localhost:5432/bpo_enrichment`) for pattern storage
- **Document parsing:** `python-docx`, `openpyxl`, `PyPDF2`, `pdfplumber`, `python-pptx`
- **PPTX generation:** `python-pptx` (cross-platform, no COM/Windows dependency)
- **HTTP client:** `httpx` (async)
- **GPU:** RTX 6000 PRO Blackwell (96GB VRAM) running all models simultaneously

### Frontend (Next.js Proposal Engine)
- **Framework:** Next.js 16 + React 19 + TypeScript
- **Styling:** Tailwind CSS v4
- **Orchestration:** Langbase (pipes for agents, memory for per-project RAG)
- **Research:** Perplexity API (Sonar Pro for live market intelligence, backup generation)
- **MCP client:** REST calls to backend's `/tools/{name}` endpoint

## Architecture

```
┌─────────────────────────────────────────┐
│         Next.js Frontend (:3000)         │
│  Upload → Classify → Edit → Export       │
│  ┌─────────────────────────────────────┐ │
│  │  Classification Model (3 layers)    │ │
│  │  L1: Intent Groups (FE routing)     │ │
│  │  L2: Primary Labels (9 from corpus) │ │
│  │  L3: Overlays (domain, pricing)     │ │
│  └─────────────┬───────────────────────┘ │
└────────────────┼─────────────────────────┘
                 │
    ┌────────────┼────────────┐
    ▼            ▼            ▼
┌────────┐ ┌─────────┐ ┌──────────┐
│Langbase│ │MCP Srvr │ │Perplexity│
│ Pipes  │ │ (:8420) │ │   API    │
│ Memory │ │41 tools │ │Sonar Pro │
└────────┘ └────┬────┘ └──────────┘
                │
         ┌──────┼──────┐
         ▼      ▼      ▼
      Qdrant  Ollama  PostgreSQL
      600K+   96GB    Patterns
      claims  VRAM
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

### `src/slide_library.py` (slide library manager)
- `SlideLibraryManager` indexes theme-organized slide directories
- Classifies slides to 3-layer taxonomy using keyword matching
- Resolves `operational_details` fan-out to specific backend sections
- Search by keyword, theme, label, or backend section
- `select_slides_for_proposal()` picks best slides per section

### `src/pptx_builder.py` (PPTX generation)
- `analyze_template()` discovers layouts and placeholders (cross-platform, no COM)
- `ProposalDeckBuilder` orchestrates full proposal deck assembly
- Template-first workflow: analyze → populate → assemble → save
- `parse_formatted_text()` converts HTML-like tags to python-pptx runs
- `clone_slide_from_file()` copies slides from library into target deck
- Speaker notes for traceability (evidence IDs, proof tiers, sources)
- Brand colors from `BRAND_COLORS` dict (matches frontend tokens)

### `src/pptx_tools.py` (PPTX MCP tools)
- 8 MCP tool definitions + handlers for slide library and PPTX builder
- Follows same dispatch pattern as `document_tools.py`
- Active deck state managed at module level (`_active_builder`)

## MCP Tools (41+ total, 9 categories)

| Category | Tools | Purpose |
|----------|-------|---------|
| Core Search | `search_claims`, `search_by_persona`, `enrich_section`, `convert_to_practitioner_voice` | Evidence discovery |
| Style Guide | `get_style_guide`, `get_narrative_templates`, `check_voice`, `build_section`, `get_response_template`, `search_style_patterns` | Writing standards |
| Research & Validation | `get_research_guidelines`, `validate_claim`, `check_qdrant_coverage`, `format_sourced_content`, `check_content_compliance`, `get_solution_options`, `get_foundever_evidence`, `get_outcome_based_pricing_framing` | Quality assurance |
| No-Fabrication | `get_no_fabrication_policy`, `generate_iteration_request`, `check_for_fabrication`, `llm_fact_check` | Content integrity |
| RFP Input | `parse_rfp_requirements`, `generate_clarifying_questions`, `map_to_style_guide_structure`, `track_assumptions`, document parsing tools | Document processing |
| Financial Services | `get_finserv_persona`, `get_threat_context`, `get_finserv_metrics` | Domain expertise |
| Generation | `generate_rfp_response` | LLM-powered proposal writing |
| Slide Library | `index_slide_library`, `search_slide_library`, `get_slide_library_stats` | Theme-organized reference slides |
| PPTX Builder | `analyze_pptx_template`, `create_proposal_deck`, `add_proposal_slide`, `clone_library_slide`, `save_proposal_deck` | Proposal deck assembly & export |

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
# Backend (Python)
black src/              # Formatting
ruff check src/         # Linting
mypy src/               # Type checking
pytest archive/tests/   # Tests
python src/main.py --section "collections"  # CLI testing

# Frontend (Next.js)
cd frontend
npm run dev             # Dev server with Turbopack (:3000)
npm run build           # Production build
npm run typecheck       # TypeScript type checking
npm run lint            # ESLint
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

## FE Classification Model (3-Layer Taxonomy)

Derived from corpus analysis of ~1,000 RFP proposal slides. Lives in `frontend/src/lib/classification/`.

### Layer 2 — Primary Labels (classifier output, core taxonomy)

| Label | Corpus % | Description |
|-------|----------|-------------|
| **Operational Details** | ~47.5% | Processes, workflows, staffing, facilities, day-to-day execution |
| **Solution Overview** | ~21% | Capabilities, offerings, platform/ecosystem summaries |
| **Case Study** | ~11% | Client examples, outcomes, proof points |
| **Compliance / Security** | ~7% | Certifications, regulatory frameworks, risk controls |
| **Project Plan** | ~5.5% | Implementation, transition, timelines |
| **Executive Summary** | ~4.5% | High-level framing, strategic overview |
| **Other** | ~3.5% | Section dividers, low semantic payload |
| **Pricing** | Flag-based | Orthogonal — detected as `pricingFlag`, not a primary label |

### Layer 1 — Intent Groups (FE routing)

| Group | Member Labels | Backend Sections |
|-------|--------------|-----------------|
| Narrative & Positioning | exec_summary, solution_overview | 1, 2, 3 |
| Solution Definition | solution_overview, operational_details | 3, 4, 5 |
| Execution & Delivery | operational_details, project_plan | 4, 7, 8 |
| Risk & Assurance | compliance_security | 6 |
| Proof & Validation | case_study | 9 |
| Commercial Mechanics | pricing | (excluded from body) |

### Layer 3 — Overlays (secondary attributes)

- **Domain:** financial_services, banking, fintech, payments, fraud_aml_kyc, collections, insurance, healthcare, general
- **Pricing flag:** has_pricing / pricing_adjacent / no_pricing
- **Confidence:** high / medium / low

### FE → Backend Mapping

The FE's `map_to_style_guide_structure` backend tool provides the canonical 9-section structure. The FE classification maps each primary label to one or more backend sections. Key: `operational_details` (47.5% of content) fans out across delivery_model, team_leadership, solution_overview, and technology using keyword refinement in `refineToSingleSection()`.

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

### Adding a new classification label (frontend)
1. Add the label to `PrimaryLabel` type in `frontend/src/lib/classification/types.ts`
2. Add the label definition in `PRIMARY_LABELS` in `taxonomy.ts` (keywords, corpus stats)
3. Add the label to an intent group in `INTENT_GROUPS` in `taxonomy.ts`
4. Add the FE→backend mapping in `LABEL_TO_SECTIONS` in `mapping.ts`
5. Update refinement signals in `refineToSingleSection()` if needed

### Adding a new domain overlay (frontend)
1. Add the domain to `DomainOverlay` type in `types.ts`
2. Add the domain definition in `DOMAIN_OVERLAYS` in `taxonomy.ts` (signal keywords)

### Adding a Langbase pipe (frontend)
1. Create the pipe in the Langbase dashboard (or via API)
2. Add a convenience method in `frontend/src/lib/langbase/client.ts`
3. Call it from the appropriate document skill or page component

### Adding a slide library theme
1. Create a folder in the slide library root with the theme name
2. Add `.pptx` files (individual slides or multi-slide decks)
3. Add matching `.txt` files with OCR text extracts (same base name)
4. Optionally add `.png` thumbnails and `.json` metadata files
5. Re-run `index_slide_library` to pick up the new theme

### Adding a PPTX builder tool
1. Define the `Tool()` object in `src/pptx_tools.py` (add to `PPTX_TOOLS` list)
2. Add the handler function (prefixed with `_handle_`)
3. Register in `handle_pptx_tool()` dispatch
4. Add convenience method in `frontend/src/lib/mcp/client.ts`

### Customizing slide deck assembly
- Template analysis is in `src/pptx_builder.py` (`analyze_template()`)
- Placeholder population uses `_apply_segments_to_text_frame()`
- Brand colors are in `BRAND_COLORS` dict (sync with `frontend/src/lib/brand/tokens.ts`)
- Section ordering is in `ProposalDeckBuilder.build_full_proposal()`

## PPTX Generation Pipeline

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│ Slide Library│     │  MCP Content │     │   PPTX       │
│ (themes/     │     │  Generation  │     │   Builder    │
│  .pptx+.txt) │     │  (33 tools)  │     │              │
└──────┬───────┘     └──────┬───────┘     └──────┬───────┘
       │                    │                    │
       ▼                    ▼                    ▼
  index_slide_       generate_rfp_        create_proposal_
  library            response             deck
       │                    │                    │
       ▼                    ▼                    ▼
  search_slide_      (content ready)      add_proposal_slide
  library                                 clone_library_slide
       │                                         │
       ▼                                         ▼
  clone_library_                          save_proposal_deck
  slide                                   → output.pptx
```

### Typical workflow:
1. `index_slide_library` → scan theme folders, classify slides
2. `search_slide_library` → find reference slides for each section
3. `create_proposal_deck` → blank or from branded template
4. For each section:
   a. `generate_rfp_response` → generate content from evidence
   b. `add_proposal_slide` → populate slide with formatted content + notes
   c. OR `clone_library_slide` → pull reference slide from library
5. `save_proposal_deck` → export to `.pptx`
