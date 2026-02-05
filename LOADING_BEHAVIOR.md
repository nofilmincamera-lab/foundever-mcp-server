# MCP Server Loading Behavior

**Question:** When the MCP is called, does it load the embedder + Searcher + Enricher?

**Short Answer:** YES - All models are **pre-loaded at startup** for instant tool calls.

---

## Loading Timeline

### 1. MCP Server Startup
**When:** `python src/mcp_server.py 8420`

**What Loads:**
```python
# Phase 1: Lightweight imports
✅ config.py (static data, no models)
✅ Starlette HTTP server
✅ MCP protocol handlers
✅ Tool definitions (metadata only)

# Phase 2: Pre-load all models (NEW BEHAVIOR)
✅ Embedder (E5-Mistral-7B) - 7-14 GB, ~10-30s
✅ Searcher (Qdrant client) - 50 MB, ~0.5s
✅ Enricher - 10 MB, ~0.1s
```

**Memory Usage:** ~7-14 GB (includes all models)
**Startup Time:** ~10-30 seconds (includes model loading)

---

### 2. First Tool Call Requiring Search
**Examples:** `search_claims`, `search_by_persona`, `validate_claim`

**What Happens:**
```
Tool handler calls get_lazy_searcher()
              ↓
_searcher already loaded? → Yes! (pre-loaded at startup)
              ↓
Returns cached instance immediately
              ↓
Execute search query
```

**Memory Impact:**
- **Additional:** 0 MB (already loaded)
- **Total:** Same as startup (~7-14 GB)

**Load Time:** ~0 seconds (instant - models already in memory)

---

### 3. First Tool Call Requiring Enrichment
**Examples:** `enrich_section`, `convert_to_practitioner_voice`

**What Happens:**
```
Tool handler calls get_lazy_enricher()
              ↓
_enricher already loaded? → Yes! (pre-loaded at startup)
              ↓
Returns cached instance immediately
              ↓
Execute enrichment logic
```

**Memory Impact:**
- **Additional:** 0 MB (already loaded)
- **Total:** Same as startup (~7-14 GB)

**Load Time:** ~0 seconds (instant - models already in memory)

---

### 4. All Subsequent Tool Calls

**What Happens:**
```
get_lazy_searcher() → Returns existing _searcher (pre-loaded)
get_lazy_enricher() → Returns existing _enricher (pre-loaded)
```

**Memory Impact:** 0 MB additional
**Load Time:** 0 seconds (instant)

**Note:** Since all models are pre-loaded at startup, ALL tool calls after startup are instant.

---

## Singleton Pattern (Embedder)

The Embedder uses a **singleton pattern** to ensure only ONE instance loads:

```python
class StyleGuideEmbedder:
    _instance = None          # Class-level shared instance
    _initialized = False      # Flag to prevent re-init

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if StyleGuideEmbedder._initialized:
            return  # Skip if already initialized

        # Load model (only happens once)
        self.model = AutoModel.from_pretrained(...)
        StyleGuideEmbedder._initialized = True
```

**Result:** Even if both Searcher and Enricher call `get_embedder()`, the model only loads once.

---

## Complete Loading Matrix

| Component | When Loaded | First Tool Using It | Memory | Load Time |
|-----------|-------------|---------------------|--------|-----------|
| **Config** | Server startup | All tools | ~10 MB | ~0.1s |
| **Embedder** | First search tool | `search_claims` | ~7-14 GB | ~10-30s |
| **Searcher** | First search tool | `search_claims` | ~50 MB | ~0.5s |
| **Enricher** | First enrichment tool | `enrich_section` | ~10 MB | ~0.1s |
| **Qdrant Connection** | With Searcher | `search_claims` | ~50 MB | ~0.5s |
| **Ollama (external)** | When LLM tool called | `llm_fact_check` | N/A (external process) | Per request |

---

## Tool-by-Tool Loading

### Tools That Trigger Embedder Load (First Use)

**Category: Core Search (4 tools)**
1. `search_claims` (line 1043)
2. `search_by_persona` (line 1054)
3. `check_qdrant_coverage` (line 1837)
4. `validate_claim` (line 1653)

**Category: Research (2 tools)**
5. `get_foundever_evidence` (line 1147)
6. `get_solution_options` (line 1731)

**Category: Building (1 tool)**
7. `build_section` (line 1495)

**Category: Enrichment (2 tools)**
8. `enrich_section` (line 1078) - Also loads Enricher
9. `convert_to_practitioner_voice` (line 1119) - Also loads Enricher

**First call to ANY of these 9 tools → Loads Embedder + Searcher**

### Tools That DON'T Load Anything Heavy

**Config-based tools (13 tools):**
- `get_style_guide`
- `get_taxonomy`
- `get_personas`
- `get_narrative_templates`
- `get_finserv_persona`
- `get_threat_context`
- `get_phrases`
- `get_anti_patterns`
- `get_finserv_metrics`
- `get_research_guidelines`
- `get_no_fabrication_policy`
- `get_outcome_based_pricing_framing`
- `get_response_template`

**These are instant** - just return static data from `config.py`

**Regex-based tools (11 tools):**
- `check_voice`
- `check_content_compliance`
- `check_for_fabrication`
- `format_sourced_content`
- `generate_iteration_request`
- `parse_rfp_requirements`
- `generate_clarifying_questions`
- `map_to_style_guide_structure`
- `track_assumptions`
- Document parsing tools (3)

**These are fast** - just regex/string processing

**LLM tools (2 tools):**
- `llm_fact_check` (line 2825)
- `generate_rfp_response` (line 3028)

**These call Ollama** - load time depends on Ollama (external)

---

## Practical Loading Scenarios

### Scenario 1: Claude asks for style guide
```
User: "Show me the Foundever style guide"
Tool: get_style_guide
Loads: Nothing (returns config data)
Time: <0.1s
```

### Scenario 2: Claude searches for evidence (first time)
```
User: "Find collections evidence"
Tool: search_claims
Loads: Embedder (7-14 GB) + Searcher (50 MB)
Time: 10-30 seconds
```

### Scenario 3: Claude searches again (cached)
```
User: "Find fraud evidence"
Tool: search_claims
Loads: Nothing (reuses cached Embedder + Searcher)
Time: ~1-2s (just query time)
```

### Scenario 4: Claude enriches a section (first time, after search)
```
User: "Enrich the collections section"
Tool: enrich_section
Loads: Enricher (10 MB) only
       (Embedder + Searcher already cached)
Time: ~0.1s + query time
```

### Scenario 5: Claude generates RFP response
```
User: "Generate executive summary"
Tool: generate_rfp_response
Loads: Nothing (calls external Ollama)
Time: 5-30s (depends on Ollama generation speed)
```

---

## Why Pre-Loading? (Updated Behavior)

**Previous Behavior (Lazy Loading):**
- ✅ Fast startup (1-2 seconds)
- ✅ Low initial memory (~200 MB)
- ❌ First tool call slow (10-30 seconds)
- ❌ User waits for models to load

**Current Behavior (Pre-Loading):**
- ✅ **ALL tool calls instant** (models ready)
- ✅ Predictable startup time
- ✅ No surprise delays during use
- ❌ Slower startup (10-30 seconds)
- ❌ Higher initial memory (7-14 GB)

**Trade-off:** Slower startup for instant tool performance.

---

## Performance Tips

### For Fast Startup
✅ Use config-based tools first (instant)
✅ Check what Qdrant has before searching (`get_research_guidelines`)

### For Fast Queries After First Load
✅ First search will be slow (10-30s) - this is expected
✅ All subsequent searches are fast (~1-2s)
✅ Keep MCP server running to maintain loaded models

### For Memory Management
✅ Embedder is singleton - only one copy in memory
✅ If you need to free memory, restart MCP server
✅ Consider using CPU mode if GPU memory is limited

---

## Log Messages You'll See

**Server startup (NEW):**
```
[mcp-style-guide] Starting MCP server on http://0.0.0.0:8420
[mcp-style-guide] MCP endpoint: http://0.0.0.0:8420/mcp/messages
[mcp-style-guide] Health check: http://0.0.0.0:8420/health
[mcp-style-guide]
[mcp-style-guide] Pre-loading models (this may take 10-30 seconds)...
[mcp-style-guide] ============================================================
[mcp-style-guide] PRE-LOADING MODELS AT STARTUP
[mcp-style-guide] ============================================================
[mcp-style-guide] Loading Searcher + Embedder...
[mcp-style-guide]   → E5-Mistral-7B (7-14 GB, ~10-30s)
[mcp-style-guide]   → Qdrant Client (~50 MB, ~0.5s)
[Embedder] Initializing on cuda
[Embedder] Loading model: intfloat/e5-mistral-7b-instruct
[Embedder] Model loaded. Embedding dim: 4096
[Searcher] Connected to Qdrant at localhost:6333
[mcp-style-guide] ✓ Searcher + Embedder loaded successfully
[mcp-style-guide] Loading Enricher...
[mcp-style-guide]   → Enrichment Engine (~10 MB, ~0.1s)
[mcp-style-guide] ✓ Enricher loaded successfully
[mcp-style-guide] ============================================================
[mcp-style-guide] ALL MODELS PRE-LOADED - SERVER READY
[mcp-style-guide] ============================================================
[mcp-style-guide]
[mcp-style-guide] Starting HTTP server...
```

**All tool calls:**
```
(No initialization messages - models already loaded at startup)
```

---

## Summary (Updated Behavior)

**At MCP Server Start:**
- ✅ Config: Loaded (static data)
- ✅ Embedder: **PRE-LOADED** (7-14 GB, 10-30s)
- ✅ Searcher: **PRE-LOADED** (50 MB, 0.5s)
- ✅ Enricher: **PRE-LOADED** (10 MB, 0.1s)

**At First Tool Call (Any Tool):**
- ✅ All models: **ALREADY LOADED** (instant access)
- No loading delays
- No initialization messages

**All Subsequent Calls:**
- ✅ Everything pre-loaded at startup
- ✅ Instant access
- ✅ No surprises

---

**Created:** February 5, 2026
**Purpose:** Document lazy loading behavior for Foundever MCP Server
