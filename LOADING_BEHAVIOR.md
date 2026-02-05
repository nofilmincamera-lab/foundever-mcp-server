# MCP Server Loading Behavior

**Question:** When the MCP is called, does it load the embedder + Searcher + Enricher?

**Short Answer:** NO - They are **lazy loaded** on first use, not at startup.

---

## Loading Timeline

### 1. MCP Server Startup
**When:** `python src/mcp_server.py 8420`

**What Loads:**
```python
# Only lightweight imports
✅ config.py (static data, no models)
✅ Starlette HTTP server
✅ MCP protocol handlers
✅ Tool definitions (metadata only)

# NOT loaded yet:
❌ Embedder (E5-Mistral-7B) - 0 MB
❌ Searcher (Qdrant client) - 0 MB
❌ Enricher - 0 MB
```

**Memory Usage:** ~100-200 MB (Python + dependencies)
**Startup Time:** ~1-2 seconds

---

### 2. First Tool Call Requiring Search
**Examples:** `search_claims`, `search_by_persona`, `validate_claim`

**What Happens:**
```
Tool handler calls get_lazy_searcher()
              ↓
_searcher is None? → Yes!
              ↓
logger.info("Initializing searcher (first use)...")
              ↓
get_searcher() from search.py
              ↓
StyleGuideSearcher.__init__()
              ↓
    self.client = QdrantClient(...)  # Lightweight connection
    self.embedder = get_embedder()   # HEAVY LOAD HERE
              ↓
StyleGuideEmbedder.__init__()
              ↓
    Load E5-Mistral-7B model
    - AutoTokenizer.from_pretrained()
    - AutoModel.from_pretrained()
    - Move to GPU (if available)
    - Set to eval mode
```

**Memory Impact:**
- **Embedder:** ~7-14 GB VRAM/RAM (E5-Mistral-7B)
- **Searcher:** ~50 MB (Qdrant client)
- **Total:** ~7-14 GB first load

**Load Time:** ~10-30 seconds (depends on GPU/CPU)

---

### 3. First Tool Call Requiring Enrichment
**Examples:** `enrich_section`, `convert_to_practitioner_voice`

**What Happens:**
```
Tool handler calls get_lazy_enricher()
              ↓
_enricher is None? → Yes!
              ↓
logger.info("Initializing enricher (first use)...")
              ↓
get_enricher() from enrichment_engine.py
              ↓
StyleGuideEnricher.__init__()
              ↓
    self.searcher = get_searcher()  # Calls get_lazy_searcher()
              ↓
    If searcher not yet loaded:
        → Loads Embedder + Searcher (see above)
    If searcher already loaded:
        → Reuses existing instance
```

**Memory Impact:**
- **Enricher:** ~10 MB (Python object)
- **Searcher:** 0 MB (reuses existing if already loaded)
- **Embedder:** 0 MB (singleton, only loads once)

**Load Time:** ~0.1 seconds (if searcher already loaded)

---

### 4. Subsequent Tool Calls

**What Happens:**
```
get_lazy_searcher() → Returns existing _searcher (cached)
get_lazy_enricher() → Returns existing _enricher (cached)
```

**Memory Impact:** 0 MB additional
**Load Time:** 0 seconds (instant)

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

## Why Lazy Loading?

**Problem without lazy loading:**
- Server startup would take 10-30 seconds
- Memory usage would be 7-14 GB from the start
- Many tools don't need the embedder at all

**Solution with lazy loading:**
- Server starts in 1-2 seconds
- Memory starts at ~200 MB
- Only loads heavy models when actually needed
- Tools that don't need models are instant

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

**Server startup:**
```
[mcp-style-guide] Starting MCP server on port 8420
```

**First search tool:**
```
[Searcher] Initializing searcher (first use)...
[Embedder] Initializing on cuda
[Embedder] Loading model: intfloat/e5-mistral-7b-instruct
[Embedder] Model loaded. Embedding dim: 4096
[Searcher] Connected to Qdrant at localhost:6333
```

**First enrichment tool (if search not yet used):**
```
[Enricher] Initializing enricher (first use)...
[Searcher] Initializing searcher (first use)...
[Embedder] Initializing on cuda
... (same as above)
```

**Subsequent calls:**
```
(No initialization messages - uses cached instances)
```

---

## Summary

**At MCP Server Start:**
- ❌ Embedder: NOT loaded
- ❌ Searcher: NOT loaded
- ❌ Enricher: NOT loaded
- ✅ Config: Loaded (static data only)

**At First Search Tool Call:**
- ✅ Embedder: Loaded (7-14 GB, 10-30s)
- ✅ Searcher: Loaded (50 MB, 0.5s)
- ❌ Enricher: NOT loaded (unless enrichment tool)

**At First Enrichment Tool Call:**
- ✅ Embedder: Loaded if not already (or reuses cached)
- ✅ Searcher: Loaded if not already (or reuses cached)
- ✅ Enricher: Loaded (10 MB, 0.1s)

**All Subsequent Calls:**
- Everything cached, instant access

---

**Created:** February 5, 2026
**Purpose:** Document lazy loading behavior for Foundever MCP Server
