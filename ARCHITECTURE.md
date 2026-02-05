# Foundever MCP Server - Architecture & Workflow

**Complete code review and workflow mapping**
**Date:** February 5, 2026

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Python Modules](#python-modules)
3. [MCP Tools (33 Total)](#mcp-tools-33-total)
4. [Prompt Usage](#prompt-usage)
5. [Data Flow Diagrams](#data-flow-diagrams)
6. [Tool Call Workflows](#tool-call-workflows)
7. [External Dependencies](#external-dependencies)

---

## System Overview

The Foundever MCP Server is a Model Context Protocol server that provides 33 specialized tools for generating professional RFP responses using Foundever's established writing standards.

### Core Architecture

```
┌─────────────────────────────────────────────────┐
│  Claude Desktop / MCP Client                    │
│  HTTP/SSE requests to tools                     │
└─────────────────┬───────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────┐
│  MCP Server (src/mcp_server.py)                 │
│  - 33 Tool Handlers                             │
│  - Request routing & validation                 │
│  - Async HTTP/SSE protocol                      │
└─────────────────┬───────────────────────────────┘
                  │
        ┌─────────┴──────────┬──────────────┐
        │                    │              │
┌───────▼────────┐  ┌───────▼────────┐  ┌─▼──────────┐
│ Enrichment     │  │ Search Engine   │  │ Embedder   │
│ Engine         │  │ (search.py)     │  │ (embedder) │
│ (enrichment_   │  │                 │  │            │
│  engine.py)    │  │ Qdrant Client   │  │ E5-Mistral │
└───────┬────────┘  └───────┬─────────┘  └────────────┘
        │                   │
        │           ┌───────▼─────────┐
        │           │ Qdrant Vector   │
        │           │ Database        │
        │           │ :6333           │
        │           │                 │
        │           │ - claims (600K) │
        │           │ - chunks (135K) │
        │           └─────────────────┘
        │
┌───────▼────────────────────────────────────────┐
│ Prompts Directory (prompts/)                   │
│                                                 │
│ - foundever_voice_system.txt                   │
│ - fact_check_system.txt                        │
│ - fact_check_user.txt                          │
│ - proposal_generation.txt                      │
│ - voice_conversion.txt                         │
│ - claim_enrichment.txt                         │
└────────────────────────────────────────────────┘
        │
┌───────▼────────────────────────────────────────┐
│ Ollama (localhost:11434)                       │
│                                                 │
│ - foundever-voice:latest (32B fine-tuned)      │
│ - qwen2.5:32b (fact-checking)                  │
│ - gpt-oss:120b-analytics (general LLM)         │
└─────────────────────────────────────────────────┘
```

---

## Python Modules

### 1. `src/__init__.py` (32 lines)
**Purpose:** Package initialization
**Exports:**
- CLIENT_PERSONAS, BUYER_DOMAIN_TAXONOMY, PROOF_TIERS
- StyleGuideEmbedder, get_embedder
- StyleGuideSearcher, SearchResult, get_searcher
- StyleGuideEnricher, get_enricher

### 2. `src/config.py` (810 lines)
**Purpose:** Centralized configuration and data structures

**Key Components:**
- **Database Config:** PostgreSQL connection (bpo_enrichment)
- **Qdrant Config:** Vector DB settings (localhost:6333)
- **Embedding Model:** E5-Mistral-7B-Instruct (4096-dim)
- **LLM Models:** Ollama URLs and model names
- **Prompt Loading:** `load_prompt()` function reads from `prompts/`

**Loaded Prompts:**
```python
FOUNDEVER_VOICE_SYSTEM_PROMPT = load_prompt("foundever_voice_system")
FACT_CHECK_SYSTEM_PROMPT = load_prompt("fact_check_system")
FACT_CHECK_USER_PROMPT = load_prompt("fact_check_user")
```

**Data Structures:**
- **CLIENT_PERSONAS** (8 personas): PayTech, Retail Bank, Card Issuer, Investment Bank, Insurance, Mortgage, FinTech, Collections
- **BUYER_DOMAIN_TAXONOMY** (7 domains): CX Operations, Collections, Financial Crime, Sales, Finance & Accounting, Trust & Safety, Healthcare
- **PROOF_TIERS** (4 levels): T0_marketing, T1_vendor_artifact, T2_case_study, T3_third_party_recognition
- **FINSERV_PERSONAS** (12 types): Payment Processors, Retail Banks, Card Issuers, etc.
- **NARRATIVE_TEMPLATES**: Confirmation syntax, value bridges, so-what closes
- **THREAT_CONTEXTS**: APP Fraud, Account Takeover, etc.
- **FINSERV_METRICS**: Regulatory, operational, customer experience metrics
- **ANTI_PATTERNS**: What NOT to do in proposals

### 3. `src/embedder.py` (135 lines)
**Purpose:** Generate semantic embeddings using E5-Mistral-7B

**Main Class:** `StyleGuideEmbedder` (Singleton)

**Methods:**
- `embed(text)` → Single embedding (4096-dim)
- `embed_batch(texts, prefix="query: ")` → Batch embeddings
- `embed_for_style_guide(query, context, domain)` → Optimized for enrichment

**Process Flow:**
1. Initialize model on GPU/CPU
2. Tokenize with padding/truncation (max 512 tokens)
3. Generate embeddings from model outputs
4. Mean pooling over token embeddings
5. L2 normalization
6. Return as float list

**Used By:**
- `search.py` - For semantic search queries
- All tools that perform similarity search

### 4. `src/search.py` (531 lines)
**Purpose:** Semantic search across Qdrant vector database

**Main Class:** `StyleGuideSearcher`

**Search Methods:**
1. **`search_claims()`**
   - Searches `claims` collection (600K+ vectors, 4096-dim)
   - Filters: provider, domain, proof_tier, claim_type
   - Returns: SearchResult objects with weighted scores

2. **`search_chunks()`**
   - Searches `unified_chunks` collection (135K vectors, 2048-dim)
   - Filters: provider, content_type
   - Fallback to scroll if vector search fails

3. **`search_for_persona()`**
   - Persona-tailored search
   - Enriches query with persona keywords
   - Returns results grouped by domain

4. **`search_for_style_guide_section()`**
   - Comprehensive search for enrichment
   - Multiple searches by proof tier and claim type
   - Categorizes results: high_quality, case_study, outcomes, capabilities

**SearchResult Dataclass:**
```python
@dataclass
class SearchResult:
    id: str
    score: float
    source: str  # 'claims' or 'chunks'
    text: str
    provider: str
    proof_tier: Optional[str]
    content_type: Optional[str]
    domain: Optional[str]
    metadata: Dict[str, Any]

    @property
    def weighted_score(self) -> float:
        # Applies proof tier weights to raw similarity score
```

### 5. `src/enrichment_engine.py` (513 lines)
**Purpose:** Enrich RFP sections with evidence from Qdrant

**Main Class:** `StyleGuideEnricher`

**Core Methods:**

1. **`_call_llm(prompt, max_tokens=500)`**
   - Calls Ollama (gpt-oss:120b-analytics)
   - Used for generating refined templates
   - Temperature: 0.3 (low variance)

2. **`_extract_metrics_from_text(text)`**
   - Regex patterns for percentages, dollars, time, ratios
   - Returns list of metrics with context

3. **`_convert_to_persona_example(claim, target_persona)`**
   - Converts generic claim to persona-specific example
   - Applies persona framing
   - Returns EnrichedExample object

4. **`_identify_foundever_patterns(claims)`**
   - Analyzes claims for Foundever-specific patterns
   - Tracks domains, proof distribution, value propositions
   - Identifies differentiators from high-tier outcomes

5. **`enrich_section(section_topic, target_personas, use_llm=False)`**
   - Main enrichment workflow
   - Searches for evidence by persona and domain
   - Generates persona-specific examples
   - Returns StyleGuideEnrichment object

6. **`convert_to_practitioner_voice(marketing_phrase, persona, domain)`**
   - Converts marketing language to specific claims
   - Searches for evidence claims matching topic
   - **Uses LLM with `voice_conversion` prompt** (if use_llm=True)
   - Returns converted text with sources

**Prompt Usage:**
```python
# In convert_to_practitioner_voice()
prompt = f"""Convert this marketing phrase to practitioner voice for a {persona_info['display_name']}:

Marketing phrase: {marketing_phrase}

Example claims about this topic:
{claims}

Convert to specific, evidence-based practitioner voice with:
- Concrete numbers and metrics
- Source attribution [Source]
- No superlatives or marketing language
- {{placeholders}} for unknown specifics"""
```

### 6. `src/document_tools.py` (682 lines)
**Purpose:** RFP document parsing (Word, Excel, PDF)

**Tool Functions:**
- `extract_text_from_word(file_path)` - DOCX parsing
- `extract_text_from_excel(file_path)` - XLSX table extraction
- `extract_text_from_pdf(file_path)` - PDF text extraction

**Used By:** MCP tools for parsing uploaded RFP documents

### 7. `src/main.py` (394 lines)
**Purpose:** CLI interface for testing (not used by MCP server)

**Commands:**
- Search claims by query
- Search by persona
- Enrich sections
- Convert marketing to practitioner voice

### 8. `src/overnight_test.py` (537 lines)
**Purpose:** Test harness for overnight evaluation

**Test Scenarios:**
- Generate proposal sections using Ollama
- Fact-check generated content
- **Uses inline prompts** (similar to prompt files)

**Prompts Used:**
1. **Proposal Generation Prompt** (line 112)
   ```python
   prompt = f"""You are a Foundever RFP response writer. Generate a proposal section...
   RULES (CRITICAL):
   1. Use {{placeholder}} for ANY specific numbers
   2. NEVER fabricate statistics
   3. Every statistic MUST have [Source] attribution
   ```

2. **Fact-Check Prompt** (line 156)
   ```python
   prompt = f"""You are a rigorous fact-checker for RFP proposals...
   CHECK FOR:
   1. FABRICATED STATISTICS
   2. PRICING VIOLATIONS
   3. UNSOURCED CLAIMS
   ```

### 9. `src/mcp_server.py` (3,228 lines) 🔥 **MAIN FILE**
**Purpose:** MCP protocol server with 33 tools

**Server Setup:**
- Framework: Starlette (async HTTP)
- Transport: SSE (Server-Sent Events) for MCP
- Port: 8420
- Endpoints: `/mcp` (SSE), `/health`, `/info`, `/tool` (REST)

**Tool Handler:** `async def handle_tool_call(name: str, arguments: Dict[str, Any]) -> str`

---

## MCP Tools (33 Total)

### Category 1: Core Search Tools (4 tools)

#### 1. `search_claims`
**Handler:** Line 1038
**Purpose:** Semantic search across 600K+ claims
**Flow:**
```
Claude requests → MCP handler → get_lazy_searcher() → searcher.search_claims()
                                                     ↓
                                           Embedder generates query vector
                                                     ↓
                                           Qdrant similarity search
                                                     ↓
                                           Returns SearchResult objects
```
**Filters:** query, domain, provider, proof_tier, limit
**Returns:** List of claims with metadata, scores, sources

#### 2. `search_by_persona`
**Handler:** Line 1053
**Purpose:** Persona-tailored evidence search
**Flow:**
```
Claude → MCP → searcher.search_for_persona()
                     ↓
          Enriches query with persona keywords
                     ↓
          Searches each relevant domain
                     ↓
          Groups results by domain
```
**Input:** persona (paytech, retail_bank, etc.), query
**Returns:** Dict of domain → results

#### 3. `enrich_section`
**Handler:** Line 1077
**Purpose:** Comprehensive section enrichment
**Flow:**
```
Claude → MCP → get_lazy_enricher() → enricher.enrich_section()
                                              ↓
                                    Searches for high-quality claims
                                              ↓
                                    Searches case study evidence
                                              ↓
                                    Generates persona examples
                                              ↓
                                    Identifies Foundever patterns
                                              ↓
                                    (Optional) LLM template generation
                                              ↓
                                    Returns StyleGuideEnrichment
```
**Prompt Used:** `claim_enrichment.txt` (if use_llm=True)

#### 4. `convert_to_practitioner_voice`
**Handler:** Line 1118
**Purpose:** Convert marketing phrases to specific claims
**Flow:**
```
Claude → MCP → enricher.convert_to_practitioner_voice()
                            ↓
                  Search for evidence on topic
                            ↓
                  (Optional) LLM voice conversion
                            ↓
                  Format with sources
```
**Prompt Used:** `voice_conversion.txt` (if use_llm=True)

### Category 2: Style Guide Tools (6 tools)

#### 5. `get_style_guide`
**Handler:** Line 1215
**Purpose:** Returns complete Foundever RFP Style Guide
**Source:** config.py static data
**Returns:** Markdown formatted guide with:
- 1 Plus Structure
- Voice guidelines
- Proof tier system
- Section templates

#### 6. `get_narrative_templates`
**Handler:** Line 1309
**Purpose:** Returns narrative pattern templates
**Source:** config.NARRATIVE_TEMPLATES
**Returns:** Confirmation syntax, value bridges, so-what closes

#### 7. `check_voice`
**Handler:** Line 1326
**Purpose:** Analyze text for marketing vs practitioner voice
**Process:**
1. Scans for marketing phrases (config.PHRASES_TO_AVOID)
2. Scans for AI-sounding language
3. Identifies unsourced statistics
4. Returns flagged issues with suggestions

#### 8. `build_section`
**Handler:** Line 1480
**Purpose:** Generate structured proposal section
**Flow:**
```
Claude → MCP → Search evidence for topic
                      ↓
            Apply section template structure:
            - Framing statement
            - Key metrics table
            - The Point section
            - Supporting detail
            - Value statement
                      ↓
            Format with evidence sources
```
**Output:** Markdown formatted section

#### 9. `get_response_template`
**Handler:** Line 2656
**Purpose:** Get compliant response template for section type
**Templates:** Executive Summary, Technical, Case Study, Pricing Discussion

#### 10. `search_style_patterns`
**Handler:** Line 2902
**Purpose:** Search Foundever voice model patterns
**Process:** Queries PostgreSQL for narrative templates from training data

### Category 3: Research & Validation Tools (8 tools)

#### 11. `get_research_guidelines`
**Handler:** Line 1545
**Purpose:** **CRITICAL** - Returns research protocol
**Source:** config.RESEARCH_GUIDELINES
**Priority Hierarchy:**
1. User-provided info
2. Style guide templates
3. Qdrant evidence
4. External research (with iteration)

#### 12. `validate_claim`
**Handler:** Line 1648
**Purpose:** Validate claim against Qdrant database
**Confidence Levels:**
- **VALIDATED:** T2+ evidence or user confirmation
- **TENTATIVE:** T0-T1 evidence, needs verification
- **UNVALIDATED:** No evidence found
- **FABRICATED:** Contradicts evidence

#### 13. `check_qdrant_coverage`
**Handler:** Line 1832
**Purpose:** Check what evidence exists before external research
**Returns:** Count by proof tier, sample claims, gaps

#### 14. `format_sourced_content`
**Handler:** Line 1915
**Purpose:** Add proper [Source] attribution to content

#### 15. `check_content_compliance`
**Handler:** Line 1958
**Purpose:** Scan for pricing violations and unsourced stats
**Violations:**
- Pricing mentions (FORBIDDEN)
- Unsourced statistics
- Missing placeholders
- Style guide violations

#### 16. `get_solution_options`
**Handler:** Line 1719
**Purpose:** Generate 2-3 solution options (not prescriptive)
**Process:** Searches evidence, generates options with tradeoffs

#### 17. `get_foundever_evidence`
**Handler:** Line 1146
**Purpose:** Get comprehensive Foundever evidence package
**Returns:** Claim counts, proof tier distribution, top domains

#### 18. `get_outcome_based_pricing_framing`
**Handler:** Line 2073
**Purpose:** Get approved outcome-based pricing talking points
**Note:** ONLY pricing topic allowed

### Category 4: No-Fabrication Tools (4 tools)

#### 19. `get_no_fabrication_policy`
**Handler:** Line 2124
**Purpose:** Returns strict no-fabrication rules
**Rules:**
- Never fabricate statistics
- Use {{placeholders}} for unknowns
- Every claim needs [Source]
- Iterate with user for missing data

#### 20. `generate_iteration_request`
**Handler:** Line 2177
**Purpose:** Generate structured request for missing info
**Process:** Lists what's needed, templates for user to fill

#### 21. `check_for_fabrication`
**Handler:** Line 2227
**Purpose:** Scan content for fabricated information
**Detects:**
- Specific numbers without [Source]
- Suspiciously precise statistics
- Unsourced comparatives
- Missing {{placeholders}}

#### 22. `llm_fact_check` 🔥
**Handler:** Line 2825
**Purpose:** **FINAL PASS** - LLM-powered fact-checking
**Model:** qwen2.5:32b via Ollama
**Prompts Used:**
1. **`FACT_CHECK_SYSTEM_PROMPT`** (fact_check_system.txt)
2. **`FACT_CHECK_USER_PROMPT`** (fact_check_user.txt)

**Flow:**
```
Claude → MCP → Format prompts:
                 system = FACT_CHECK_SYSTEM_PROMPT
                 user = FACT_CHECK_USER_PROMPT.format(
                     content=content_to_check,
                     evidence=evidence_found
                 )
                      ↓
               Call Ollama (httpx.AsyncClient)
                      ↓
               Parse JSON response
                      ↓
               Return fact-check results with:
               - fabricated_stats
               - pricing_violations
               - unsourced_claims
               - overall_score (1-10)
               - pass_fail
```

**Implementation (Line 2839):**
```python
user_prompt = FACT_CHECK_USER_PROMPT.format(
    content=content,
    evidence=evidence_summary
)

full_prompt = f"{FACT_CHECK_SYSTEM_PROMPT}\n\n{user_prompt}"

async with httpx.AsyncClient(timeout=120.0) as client:
    response = await client.post(
        OLLAMA_URL,
        json={
            "model": FACT_CHECK_MODEL,  # qwen2.5:32b
            "prompt": full_prompt,
            "stream": False
        }
    )
```

### Category 5: RFP Input Handling Tools (8 tools)

#### 23. `parse_rfp_requirements`
**Handler:** Line 2324
**Purpose:** Parse requirements from RFP documents
**Process:**
1. Takes extracted text from Word/Excel/PDF
2. Identifies discrete requirements
3. Categorizes by type
4. Extracts metadata

#### 24. `generate_clarifying_questions`
**Handler:** Line 2405
**Purpose:** Generate questions for ambiguous requirements
**Categories:**
- Ambiguous scope
- Missing metrics
- Undefined terms
- Timeline uncertainties

#### 25. `map_to_style_guide_structure`
**Handler:** Line 2504
**Purpose:** Map requirements to proposal structure
**Sections:**
- Executive Summary (1 Plus)
- Technical Approach
- Experience & Credentials
- Management Plan
- Pricing Discussion

#### 26. `track_assumptions`
**Handler:** Line 2608
**Purpose:** Log assumptions needing confirmation
**Tracks:**
- Assumption made
- Confidence level
- Impact if incorrect
- Verification needed

#### 27-29. **Document Tool Wrappers** (Handled by document_tools.py)
- Parse Word documents
- Parse Excel spreadsheets
- Parse PDF files

### Category 6: Financial Services Tools (3 tools)

#### 30. `get_finserv_persona`
**Handler:** Line 1371
**Purpose:** Get detailed FinServ persona information
**Personas:** 12 types (Payment Processors, Retail Banks, Card Issuers, etc.)

#### 31. `get_threat_context`
**Handler:** Line 1399
**Purpose:** Get threat descriptions for proposals
**Threats:** APP Fraud, Account Takeover, Identity Fraud, etc.

#### 32. `get_finserv_metrics`
**Handler:** Line 1464
**Purpose:** Get metrics that matter for FinServ
**Categories:** Regulatory, operational, customer experience

### Category 7: Generation Tools (1 tool)

#### 33. `generate_rfp_response` 🔥
**Handler:** Line 3028
**Purpose:** Generate RFP section using Foundever Voice Model
**Model:** foundever-voice:latest (32B fine-tuned)
**Prompt Used:** `FOUNDEVER_VOICE_SYSTEM_PROMPT` (foundever_voice_system.txt)

**Flow:**
```
Claude → MCP → Parse requirement by section type
                      ↓
             Build prompt with section template
                      ↓
             Call Ollama (foundever-voice:latest)
               system = FOUNDEVER_VOICE_SYSTEM_PROMPT
               prompt = section_prompt + requirement
                      ↓
             Generate response
                      ↓
             Return formatted output
```

**Implementation (Line 3062):**
```python
async with httpx.AsyncClient(timeout=180.0) as client:
    response = await client.post(
        OLLAMA_URL,
        json={
            "model": FOUNDEVER_VOICE_MODEL,  # foundever-voice:latest
            "prompt": prompt,
            "system": FOUNDEVER_VOICE_SYSTEM_PROMPT,
            "stream": False,
            "options": {
                "temperature": 0.7,
                "top_p": 0.9,
                "num_predict": 2000
            }
        }
    )
```

---

## Prompt Usage

### Prompt Files → Code Mapping

| Prompt File | Loaded By | Used By | Purpose |
|-------------|-----------|---------|---------|
| `foundever_voice_system.txt` | config.py:69 | mcp_server.py:3069 | System prompt for Foundever Voice model |
| `fact_check_system.txt` | config.py:72 | mcp_server.py:2844 | System prompt for fact-checking |
| `fact_check_user.txt` | config.py:73 | mcp_server.py:2839 | User template for fact-checking |
| `proposal_generation.txt` | ❌ Not loaded | overnight_test.py:112 | Test harness only (inline) |
| `voice_conversion.txt` | ❌ Not loaded | enrichment_engine.py:386 | Inline in convert function |
| `claim_enrichment.txt` | ❌ Not loaded | enrichment_engine.py:309 | Inline in enrich function |

### Prompt Usage Locations

#### 1. Foundever Voice System Prompt
**File:** `prompts/foundever_voice_system.txt`
**Loaded:** `src/config.py` line 69
```python
FOUNDEVER_VOICE_SYSTEM_PROMPT = load_prompt("foundever_voice_system")
```

**Used:** `src/mcp_server.py` line 3069 in `generate_rfp_response` tool
```python
"system": FOUNDEVER_VOICE_SYSTEM_PROMPT,
```

**Purpose:** Defines the Foundever RFP writing voice for the fine-tuned model

#### 2. Fact-Check System Prompt
**File:** `prompts/fact_check_system.txt`
**Loaded:** `src/config.py` line 72
```python
FACT_CHECK_SYSTEM_PROMPT = load_prompt("fact_check_system")
```

**Used:** `src/mcp_server.py` line 2844 in `llm_fact_check` tool
```python
full_prompt = f"{FACT_CHECK_SYSTEM_PROMPT}\n\n{user_prompt}"
```

**Purpose:** System prompt for rigorous fact-checking

#### 3. Fact-Check User Prompt
**File:** `prompts/fact_check_user.txt`
**Loaded:** `src/config.py` line 73
```python
FACT_CHECK_USER_PROMPT = load_prompt("fact_check_user")
```

**Used:** `src/mcp_server.py` line 2839 in `llm_fact_check` tool
```python
user_prompt = FACT_CHECK_USER_PROMPT.format(
    content=content,
    evidence=evidence_summary
)
```

**Purpose:** User-side template for fact-checking requests

#### 4-6. Prompts NOT Currently Loaded
**Files:**
- `prompts/proposal_generation.txt`
- `prompts/voice_conversion.txt`
- `prompts/claim_enrichment.txt`

**Status:** These prompts exist in files but are currently defined inline in the code:
- `proposal_generation.txt` → `overnight_test.py:112` (inline)
- `voice_conversion.txt` → `enrichment_engine.py:386` (inline)
- `claim_enrichment.txt` → `enrichment_engine.py:309` (inline)

**Recommendation:** Update code to use `load_prompt()` for these files

---

## Data Flow Diagrams

### 1. Search Claim Flow

```
┌──────────────┐
│ Claude       │
│ "search for  │
│  collections │
│  evidence"   │
└──────┬───────┘
       │
       ▼
┌──────────────────────────────────────┐
│ MCP Server: search_claims handler   │
│ Line 1038                            │
└──────┬───────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────┐
│ Get Searcher (lazy load)             │
│ searcher = get_lazy_searcher()       │
└──────┬───────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────┐
│ StyleGuideSearcher.search_claims()   │
│ src/search.py:55                     │
└──────┬───────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────┐
│ Embedder: Generate query vector      │
│ embedder.embed(query)                │
│ → 4096-dim float vector              │
└──────┬───────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────┐
│ Qdrant: Vector similarity search     │
│ collection: "claims"                 │
│ query_vector: [4096 floats]          │
│ filters: domain, provider, tier      │
└──────┬───────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────┐
│ Convert to SearchResult objects      │
│ - Extract payload metadata           │
│ - Calculate weighted scores          │
│ - Sort by relevance                  │
└──────┬───────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────┐
│ Format as JSON response              │
│ Return to Claude via MCP             │
└──────────────────────────────────────┘
```

### 2. LLM Fact-Check Flow

```
┌──────────────┐
│ Claude       │
│ "fact-check  │
│  this        │
│  content"    │
└──────┬───────┘
       │
       ▼
┌────────────────────────────────────────┐
│ MCP Server: llm_fact_check handler    │
│ Line 2825                              │
└──────┬─────────────────────────────────┘
       │
       ▼
┌────────────────────────────────────────┐
│ Load Prompts from config               │
│ - FACT_CHECK_SYSTEM_PROMPT             │
│ - FACT_CHECK_USER_PROMPT               │
│   (loaded from prompts/ directory)     │
└──────┬─────────────────────────────────┘
       │
       ▼
┌────────────────────────────────────────┐
│ Format User Prompt                     │
│ user_prompt = FACT_CHECK_USER_PROMPT   │
│   .format(                             │
│     content=content_to_check,          │
│     evidence=evidence_found            │
│   )                                    │
└──────┬─────────────────────────────────┘
       │
       ▼
┌────────────────────────────────────────┐
│ Combine Prompts                        │
│ full_prompt = f"{SYSTEM}\n\n{USER}"    │
└──────┬─────────────────────────────────┘
       │
       ▼
┌────────────────────────────────────────┐
│ Call Ollama API                        │
│ POST http://localhost:11434/api/generate│
│ {                                      │
│   "model": "qwen2.5:32b",              │
│   "prompt": full_prompt,               │
│   "stream": false                      │
│ }                                      │
└──────┬─────────────────────────────────┘
       │
       ▼
┌────────────────────────────────────────┐
│ Parse JSON Response                    │
│ Extract:                               │
│ - fabricated_stats: []                 │
│ - pricing_violations: []               │
│ - unsourced_claims: []                 │
│ - overall_score: 1-10                  │
│ - pass_fail: "PASS" or "FAIL"          │
└──────┬─────────────────────────────────┘
       │
       ▼
┌────────────────────────────────────────┐
│ Format Results as Markdown             │
│ Return to Claude via MCP               │
└────────────────────────────────────────┘
```

### 3. Generate RFP Response Flow

```
┌──────────────┐
│ Claude       │
│ "generate    │
│  executive   │
│  summary"    │
└──────┬───────┘
       │
       ▼
┌────────────────────────────────────────┐
│ MCP Server: generate_rfp_response      │
│ Line 3028                              │
└──────┬─────────────────────────────────┘
       │
       ▼
┌────────────────────────────────────────┐
│ Parse Section Type                     │
│ - executive_summary                    │
│ - technical_approach                   │
│ - experience                           │
│ - management_plan                      │
│ - pricing                              │
└──────┬─────────────────────────────────┘
       │
       ▼
┌────────────────────────────────────────┐
│ Build Section-Specific Prompt          │
│ prompt = section_prompts[type] +       │
│          requirement                   │
└──────┬─────────────────────────────────┘
       │
       ▼
┌────────────────────────────────────────┐
│ Load Foundever Voice System Prompt     │
│ system = FOUNDEVER_VOICE_SYSTEM_PROMPT │
│ (from prompts/foundever_voice_system)  │
└──────┬─────────────────────────────────┘
       │
       ▼
┌────────────────────────────────────────┐
│ Call Ollama with Foundever Model      │
│ POST http://localhost:11434/api/generate│
│ {                                      │
│   "model": "foundever-voice:latest",   │
│   "system": FOUNDEVER_VOICE_SYSTEM,    │
│   "prompt": prompt,                    │
│   "options": {                         │
│     "temperature": 0.7,                │
│     "top_p": 0.9,                      │
│     "num_predict": 2000                │
│   }                                    │
│ }                                      │
└──────┬─────────────────────────────────┘
       │
       ▼
┌────────────────────────────────────────┐
│ Parse Generated Response               │
│ Extract model output                   │
└──────┬─────────────────────────────────┘
       │
       ▼
┌────────────────────────────────────────┐
│ Format as Markdown Section             │
│ - Add section header                   │
│ - Preserve model structure             │
│ - Return to Claude via MCP             │
└────────────────────────────────────────┘
```

### 4. Enrich Section Flow

```
┌──────────────┐
│ Claude       │
│ "enrich      │
│  collections │
│  section"    │
└──────┬───────┘
       │
       ▼
┌────────────────────────────────────────┐
│ MCP Server: enrich_section handler    │
│ Line 1077                              │
└──────┬─────────────────────────────────┘
       │
       ▼
┌────────────────────────────────────────┐
│ Get Enricher (lazy load)               │
│ enricher = get_lazy_enricher(use_llm)  │
└──────┬─────────────────────────────────┘
       │
       ▼
┌────────────────────────────────────────┐
│ StyleGuideEnricher.enrich_section()    │
│ src/enrichment_engine.py:198           │
└──────┬─────────────────────────────────┘
       │
       ├─────────────────────────────────┐
       │                                 │
       ▼                                 ▼
┌──────────────┐              ┌──────────────────┐
│ Search       │              │ Search Case      │
│ High-Quality │              │ Study Evidence   │
│ Claims (T1+) │              │ (T2)             │
└──────┬───────┘              └──────┬───────────┘
       │                              │
       └──────────┬───────────────────┘
                  │
                  ▼
       ┌────────────────────────────────┐
       │ For Each Target Persona:       │
       │ - Search by persona keywords   │
       │ - Search by domain             │
       │ - Convert claims to examples   │
       └──────┬─────────────────────────┘
              │
              ▼
       ┌────────────────────────────────┐
       │ Extract Metrics                │
       │ - Percentages                  │
       │ - Dollar amounts               │
       │ - Time values                  │
       │ - Ratios                       │
       └──────┬─────────────────────────┘
              │
              ▼
       ┌────────────────────────────────┐
       │ Identify Foundever Patterns    │
       │ - Common domains               │
       │ - Proof distribution           │
       │ - Value propositions           │
       │ - Differentiators              │
       └──────┬─────────────────────────┘
              │
              ▼
       ┌────────────────────────────────┐
       │ IF use_llm = True:             │
       │   Call Ollama for template     │
       │   generation with              │
       │   claim_enrichment prompt      │
       └──────┬─────────────────────────┘
              │
              ▼
       ┌────────────────────────────────┐
       │ Return StyleGuideEnrichment:   │
       │ - persona_examples             │
       │ - taxonomy_enrichments         │
       │ - metrics_discovered           │
       │ - foundever_specific patterns  │
       └────────────────────────────────┘
```

---

## Tool Call Workflows

### Complete Request Lifecycle

```
┌─────────────────────────────────────────────────────────────┐
│ 1. Claude Desktop / MCP Client                              │
│    - User types request                                     │
│    - Claude decides to use MCP tool                         │
│    - Sends HTTP POST to /mcp endpoint                       │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. Starlette HTTP Server (Port 8420)                       │
│    - Receives POST request                                  │
│    - Routes to SSE handler                                  │
│    - Parses MCP protocol message                            │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. MCP Server Protocol Layer                               │
│    - Validates tool exists                                  │
│    - Validates arguments against schema                     │
│    - Calls handle_tool_call(name, arguments)                │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. Tool Handler Dispatch (Line 1034)                       │
│    if name == "search_claims": → handler at line 1038      │
│    elif name == "llm_fact_check": → handler at line 2825   │
│    elif name == "generate_rfp_response": → line 3028       │
│    ... (33 total handlers)                                  │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│ 5. Tool-Specific Processing                                │
│                                                              │
│  ┌──────────────────────┐  ┌──────────────────────┐        │
│  │ A. Search Tools      │  │ B. Generation Tools   │        │
│  │ - Get searcher       │  │ - Load prompts        │        │
│  │ - Embed query        │  │ - Call Ollama         │        │
│  │ - Search Qdrant      │  │ - Parse response      │        │
│  │ - Format results     │  │ - Format output       │        │
│  └──────────────────────┘  └──────────────────────┘        │
│                                                              │
│  ┌──────────────────────┐  ┌──────────────────────┐        │
│  │ C. Enrichment Tools  │  │ D. Validation Tools   │        │
│  │ - Get enricher       │  │ - Scan content        │        │
│  │ - Search evidence    │  │ - Check rules         │        │
│  │ - Generate examples  │  │ - Flag violations     │        │
│  │ - Return enrichment  │  │ - Return report       │        │
│  └──────────────────────┘  └──────────────────────┘        │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│ 6. Response Formatting                                      │
│    - Convert to JSON string                                 │
│    - Apply MCP protocol wrapping                            │
│    - Add metadata (timing, status)                          │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│ 7. SSE Response Stream                                      │
│    - Send as Server-Sent Event                              │
│    - Claude receives and parses                             │
│    - Displays to user                                       │
└─────────────────────────────────────────────────────────────┘
```

### Tool Dependencies Map

```
search_claims ────────────┐
search_by_persona ────────┤
check_qdrant_coverage ────┤──> StyleGuideSearcher ──> Embedder ──> Qdrant
search_style_patterns ────┤
validate_claim ───────────┘

enrich_section ───────────┐
convert_to_practitioner ──┤──> StyleGuideEnricher ──> Searcher ──> Qdrant
build_section ────────────┘                          └──> Ollama (optional)

llm_fact_check ───────────┐
generate_rfp_response ────┤──> Ollama HTTP API
                          └──> Prompts (from prompts/)

get_style_guide ──────────┐
get_taxonomy ─────────────┤
get_personas ─────────────┤──> config.py (static data)
get_finserv_persona ──────┤
get_threat_context ───────┤
get_narrative_templates ──┘
```

---

## External Dependencies

### 1. Qdrant Vector Database
**Connection:** `localhost:6333`
**Collections:**
- `claims` (600K+ vectors, 4096-dim)
- `unified_chunks` (135K vectors, 2048-dim)

**Used By:** All search tools

### 2. Ollama LLM Server
**Connection:** `http://localhost:11434/api/generate`
**Models:**
- **foundever-voice:latest** (32B fine-tuned) - RFP generation
- **qwen2.5:32b** (20GB) - Fact-checking
- **gpt-oss:120b-analytics** (65GB) - Complex enrichment

**Used By:**
- `generate_rfp_response` → foundever-voice
- `llm_fact_check` → qwen2.5:32b
- `StyleGuideEnricher._call_llm()` → gpt-oss:120b-analytics

### 3. PostgreSQL Database
**Connection:** `localhost:5432/bpo_enrichment`
**Credentials:** bpo_user / bpo_secure_password_2025
**Used By:** `search_style_patterns` (narrative templates)

### 4. Python Packages
**Core:**
- `mcp` - Model Context Protocol
- `starlette` - Async HTTP framework
- `uvicorn` - ASGI server
- `sse-starlette` - Server-Sent Events

**AI/ML:**
- `torch` - PyTorch
- `transformers` - HuggingFace models
- `sentence-transformers` - E5-Mistral embeddings

**Data:**
- `qdrant-client` - Vector database client
- `psycopg2` - PostgreSQL adapter
- `httpx` - Async HTTP client (for Ollama)

**Documents:**
- `python-docx` - Word parsing
- `openpyxl` - Excel parsing
- `PyPDF2` - PDF parsing

---

## Summary

### Critical Flow Paths

**1. Search Evidence:**
```
Claude → MCP → Searcher → Embedder → Qdrant → Results
```

**2. Fact-Check Content:**
```
Claude → MCP → Load Prompts → Ollama (qwen2.5) → Parse → Results
```

**3. Generate RFP Section:**
```
Claude → MCP → Load Prompt → Ollama (foundever-voice) → Response
```

**4. Enrich Section:**
```
Claude → MCP → Enricher → Search Claims → Generate Examples → Metrics
```

### Prompt Files Actually Used
✅ **Active:**
- `foundever_voice_system.txt` → generate_rfp_response tool
- `fact_check_system.txt` → llm_fact_check tool
- `fact_check_user.txt` → llm_fact_check tool

⚠️ **Inactive (inline in code):**
- `proposal_generation.txt` → overnight_test.py only
- `voice_conversion.txt` → enrichment_engine.py (inline)
- `claim_enrichment.txt` → enrichment_engine.py (inline)

### Key Architecture Decisions
1. **Lazy Loading:** Searcher and Enricher loaded on first use (avoid startup delay)
2. **Singleton Pattern:** Embedder shared across all requests (GPU memory)
3. **Async/Await:** Full async for I/O (Qdrant, Ollama, HTTP)
4. **Weighted Scores:** Proof tiers apply multipliers to similarity scores
5. **Prompt Externalization:** System prompts loaded from files (easy updates)

---

**Generated:** February 5, 2026
**By:** Claude Code Architecture Review
