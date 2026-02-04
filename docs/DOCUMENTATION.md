# Style Guide Enrichment MCP Server - Complete Documentation

## Table of Contents
1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Components](#components)
4. [LLMs Used](#llms-used)
5. [LLM Prompts](#llm-prompts)
6. [MCP Tools Reference](#mcp-tools-reference)
7. [Dos and Don'ts](#dos-and-donts)
8. [Configuration](#configuration)
9. [Endpoints](#endpoints)

---

## Overview

The Style Guide Enrichment MCP Server is a Model Context Protocol server that helps create compliant RFP proposals by:
- Searching 600K+ claims from a Qdrant vector database
- Enforcing Foundever RFP Style Guide principles
- Preventing fabrication of statistics
- Converting marketing voice to practitioner voice
- Managing evidence with proof tiers (T0-T3)

**Key Principle**: Build narrative structure, use placeholders for unknown facts, iterate with user - NEVER fabricate.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  Claude Desktop / MCP Client                                 │
│  Connects to: https://mcp.riorock.app/mcp/messages          │
└─────────────────────┬───────────────────────────────────────┘
                      │ HTTP/SSE (GET+POST)
┌─────────────────────▼───────────────────────────────────────┐
│  MCP Server (mcp_server.py)                                  │
│  - 33 MCP Tools                                              │
│  - HTTP/SSE Transport                                        │
│  - Port 8420                                                 │
└─────────────────────┬───────────────────────────────────────┘
                      │
        ┌─────────────┼─────────────┐
        │             │             │
        ▼             ▼             ▼
┌───────────────┐ ┌───────────┐ ┌───────────────┐
│ Search Module │ │ Enricher  │ │ Config Module │
│ (search.py)   │ │ (engine)  │ │ (config.py)   │
└───────┬───────┘ └─────┬─────┘ └───────────────┘
        │               │
        ▼               ▼
┌───────────────┐ ┌───────────────┐
│ Embedder      │ │ Ollama LLM    │
│ (E5-Mistral)  │ │ (qwen2.5:32b) │
└───────┬───────┘ └───────────────┘
        │
        ▼
┌───────────────────────────────────────────────────┐
│  Qdrant Vector Database (localhost:6333)          │
│  - claims: 600K vectors (4096-dim)                │
│  - unified_chunks: 135K vectors (2048-dim)        │
└───────────────────────────────────────────────────┘
```

### Data Flow

1. **User Request** → Claude Desktop sends MCP tool call
2. **MCP Server** → Routes to appropriate handler
3. **Search/Enrich** → Queries Qdrant for evidence
4. **LLM Fact-Check** → Optional qwen2.5:32b validation
5. **Response** → Formatted with proper attribution

---

## Components

### Core Files

| File | Purpose | Size |
|------|---------|------|
| `mcp_server.py` | MCP server with 33 tools, HTTP/SSE transport | 110KB |
| `config.py` | All configuration, personas, templates, prompts | 40KB |
| `search.py` | Qdrant semantic search with proof tiers | 18KB |
| `enrichment_engine.py` | Section enrichment and voice conversion | 19KB |
| `embedder.py` | E5-Mistral-7B embedding generation | 4KB |
| `main.py` | CLI interface | 13KB |

### Supporting Files

| File | Purpose |
|------|---------|
| `overnight_test.py` | 50-scenario automated testing |
| `check_test_progress.sh` | Test monitoring script |
| `install_service.sh` | Systemd service installer |

---

## LLMs Used

### 1. Embedding Model
- **Model**: `intfloat/e5-mistral-7b-instruct`
- **Dimension**: 4096
- **Purpose**: Generate embeddings for semantic search
- **Location**: Local (runs on GPU)

### 2. Fact-Check Model
- **Model**: `qwen2.5:32b`
- **Provider**: Ollama (localhost:11434)
- **Purpose**: Final-pass fact-checking of generated content
- **Response Time**: 10-30 seconds
- **Why This Model**: Faster than 120B model (20GB vs 65GB), good for validation tasks

### 3. Main LLM (Optional)
- **Model**: `gpt-oss:120b-analytics`
- **Provider**: Ollama (localhost:11434)
- **Purpose**: Complex template generation (rarely used)
- **Note**: Most operations don't require this

---

## LLM Prompts

### Fact-Check System Prompt

```
You are a rigorous fact-checker for RFP proposals. Your job is to identify:

1. FABRICATED STATISTICS - Numbers that appear invented (no source, suspiciously precise, round numbers)
2. PRICING VIOLATIONS - ANY mention of costs, prices, savings, rates, or budgets - even as placeholders like {{$X.XM}}
3. UNSOURCED FACTUAL CLAIMS - Statistics, metrics, outcomes, or comparatives without attribution
4. MISSING PLACEHOLDERS - Specific facts that should be placeholders but aren't

IMPORTANT DISTINCTIONS:

**Needs Source (flag if missing):**
- Statistics: "99.2% accuracy", "2,500 agents"
- Metrics: "reduced AHT by 23%"
- Comparatives: "industry-leading", "best-in-class"
- Outcomes: "achieved $47M in recoveries"
- Client specifics: "supporting 4 of top 10 banks"

**Does NOT need source (do NOT flag):**
- Narrative framing: "In today's competitive landscape..."
- Logical transitions: "This approach enables..."
- General principles: "Compliance is essential for..."
- Value propositions: "Our solution will help you..."
- Conditional statements: "If implemented, this could..."

**PRICING - ABSOLUTE VIOLATION (always flag):**
- Any dollar amounts: $X, $5.5K, $X.XM
- Cost/savings mentions: "save money", "cost reduction", "estimated savings"
- Rate references: "hourly rate", "per-FTE cost"
- Even placeholders: {{$X.XM}}, {{cost savings}}, {{Estimated Cost}}

Output JSON format:
{
  "fabricated_stats": ["list of fabricated numbers without sources"],
  "pricing_violations": ["list of ANY cost/price/savings mentions"],
  "unsourced_claims": ["list of factual claims needing sources - NOT narrative framing"],
  "missing_placeholders": ["list of facts that should be {{placeholder}} format"],
  "style_violations": ["list of marketing voice or anti-pattern issues"],
  "overall_score": 1-10,
  "pass_fail": "PASS or FAIL",
  "summary": "brief explanation"
}

PASS if: No fabrications, no pricing violations, <5 minor issues
FAIL if: Any fabrications, any pricing violations, or >5 issues
```

### Fact-Check User Prompt

```
Review this content for fabricated or unsourced information.

CONTENT TO CHECK:
{content}

EVIDENCE THAT WAS ACTUALLY FOUND (if any):
{evidence}

Check every statistic, percentage, count, and specific claim. Flag anything without proper [Source] attribution.
```

---

## MCP Tools Reference

### Search Tools (8 tools)

| Tool | Purpose |
|------|---------|
| `search_claims` | Semantic search across 600K+ claims |
| `search_by_persona` | Search tailored to client persona |
| `enrich_section` | Enrich section with Qdrant evidence |
| `convert_to_practitioner_voice` | Convert marketing → practitioner voice |
| `get_foundever_evidence` | Comprehensive Foundever evidence package |
| `get_taxonomy` | Buyer domain taxonomy |
| `get_personas` | All client personas |
| `enrich_taxonomy` | Enrich taxonomy with evidence |

### Style Guide Tools (9 tools)

| Tool | Purpose |
|------|---------|
| `get_style_guide` | Complete style guide principles |
| `get_narrative_templates` | Writing pattern templates |
| `check_voice` | Analyze text for marketing voice |
| `get_finserv_persona` | FinServ persona details |
| `get_threat_context` | Threat descriptions for proposals |
| `get_phrases` | Approved/forbidden phrases |
| `get_anti_patterns` | Anti-patterns to avoid |
| `get_finserv_metrics` | FinServ metrics that matter |
| `build_section` | Generate structured section |

### Research Guidance Tools (7 tools)

| Tool | Purpose |
|------|---------|
| `get_research_guidelines` | **CALL FIRST** - Research protocol |
| `validate_claim` | Validate claim against Qdrant |
| `get_solution_options` | Generate 2-3 solution options |
| `check_qdrant_coverage` | Check before external research |
| `format_sourced_content` | Add proper attribution |
| `check_content_compliance` | Check for pricing/unsourced issues |
| `get_outcome_based_pricing_framing` | Only allowed pricing topic |

### No-Fabrication Tools (4 tools)

| Tool | Purpose |
|------|---------|
| `get_no_fabrication_policy` | **CRITICAL** - Fabrication rules |
| `generate_iteration_request` | Request missing info from user |
| `check_for_fabrication` | Scan for fabricated content |
| `llm_fact_check` | **FINAL PASS** - LLM fact-checking |

### RFP Input Handling Tools (5 tools)

| Tool | Purpose |
|------|---------|
| `parse_rfp_requirements` | Parse Word/Excel/PDF requirements |
| `generate_clarifying_questions` | Questions for ambiguous requirements |
| `map_to_style_guide_structure` | Map requirements to sections |
| `track_assumptions` | Track assumptions needing confirmation |
| `get_response_template` | Get section template |

---

## CRITICAL: Style Guide is Primary Authority

**This MCP generates RFP PROPOSALS. The Foundever RFP Style Guide is LAW.**

### Style Guide Source Files
- **Primary**: `/home/willard/Downloads/Foundever_RFP_Style_Guide.md`
- **FinServ Enrichment**: `/home/willard/Downloads/k/docs/FINANCIAL_SERVICES_ENRICHMENT.md`

### The 6 Cardinal Rules

1. **Follow style guide structure RELIGIOUSLY**
   - "1 Plus" structure: operational baseline FIRST, then included value
   - Practitioner voice: specific numbers, no superlatives
   - Every section ends with `***Value for {{Client}}:** [statement]*`

2. **Proof tiers, MCP sources, Qdrant metadata = APPENDIX ONLY**
   - Main proposal body has NO `[T2_case_study]` badges
   - NO "Qdrant returned X results" in proposal text
   - Evidence supports claims via appendix references

3. **Use {{placeholders}} liberally**
   - `{{X agents}}`, `{{X%}}`, `{{X delivery centers}}`
   - NEVER fabricate numbers - placeholder and iterate with user

4. **NEVER name specific clients unless provided in prompt**
   - Use `{{Top-10 Retail Bank}}`, `{{National Card Issuer}}`
   - In testimonials: "— Top 3 Credit Card Issuer, May 2025"

5. **Make pitch suggestions from trained persona examples**
   - For `{{National Card Issuer}}`: Lead with fraud loss containment
   - For `{{Mortgage Servicer}}`: Lead with loss mitigation outcomes
   - Based on FINSERV_PERSONAS value statements

6. **Write like the PayPal executive summary**
   - Specific, metric-backed, human-sounding
   - NO: "world-class", "cutting-edge", "seamless", "transformational"
   - YES: "2,500+ fraud agents across 10 locations supporting 7 clients"

---

## Dos and Don'ts

### DO: Source Attribution

```markdown
✅ CORRECT:
"Our 2,500 agents achieve 99.2% accuracy [Source: Internal QA Data]"
"Reduced AHT by 23% [Qdrant:T2_case_study]"
"{{X agents}} trained in TCPA [Source: TBD]"
```

```markdown
❌ WRONG:
"Our 2,500 agents achieve 99.2% accuracy" (no source)
"We have 28 delivery centers" (fabricated)
```

### DO: Use Placeholders for Unknown Data

```markdown
✅ CORRECT:
"Our team of {{X,XXX agents}} across {{X delivery centers}}"
"Reduced AHT from {{X minutes}} to {{Y minutes}}"
"{{outcome: specify metric improvement needed}}"
```

```markdown
❌ WRONG:
"Our team of 35,000 agents across 28 delivery centers" (fabricated)
```

### DON'T: Discuss Pricing

```markdown
❌ NEVER DO:
- "Cost savings of {{$X.XM}}"
- "Hourly rate of $X/hr"
- "Estimated Cost" (even as a table column)
- "ROI of {{X%}}"
- Any dollar amounts
```

```markdown
✅ INSTEAD:
- Focus on OUTCOMES: "Reduced AHT by {{X%}}"
- Focus on METRICS: "Improved FCR from {{X%}} to {{Y%}}"
- For commercial discussions: "Detailed pricing requires scope confirmation"
- ONLY exception: "Outcome-based pricing aligns incentives..."
```

### DON'T: Name Specific Clients

```markdown
❌ NEVER (unless provided in prompt):
- "We work with Chase Bank"
- "Our PayPal engagement"
- "Bank of America uses our..."
```

```markdown
✅ USE PERSONAS:
- "Our work with a {{Top-10 Retail Bank}}"
- "A {{National Card Issuer}} engagement"
- "For a leading {{Mortgage Servicer}}"

✅ IN TESTIMONIALS:
> "Foundever Compliance is heads and shoulders above the network"
> — Top 3 Credit Card Issuer, May 2025
```

### DO: Use Appendix for Evidence

**Main Proposal Body:**
```markdown
Our team of {{X,XXX agents}} across {{X delivery centers}} delivers
Right Party Contact rate of 38% vs. industry average of 22%.
```

**Appendix A: Evidence Sources:**
```markdown
- [T2_case_study] Collections performance for national card issuer, 2024
- [T3_third_party] Industry benchmark data, McKinsey Collections Report 2025
- [T1_vendor_artifact] Internal QA dashboard, Q4 2025
```

### DO: Make Pitch Suggestions

Based on trained persona examples:

| Persona | Lead With |
|---------|-----------|
| `{{Top-10 Retail Bank}}` | "Dispute resolution cycle reduced from 12 days to 7, inside Reg E timelines" |
| `{{National Card Issuer}}` | "Fraud losses contained at 3.2 bps while maintaining 94% customer satisfaction" |
| `{{Mortgage Servicer}}` | "Loss mitigation workout completion increased 23%" |
| `{{FinTech Lender}}` | "Right Party Contact rate of 38% vs. industry average of 22%" |
| `{{Insurance Carrier}}` | "FNOL cycle time reduced from 48 hours to 6 hours" |
| `{{Payment Processor}}` | "Merchant onboarding SLA compliance at 99.1%" |

### DON'T: Use Marketing Voice

```markdown
❌ AVOID:
- "World-class fraud prevention"
- "Industry-leading technology"
- "Seamless integration"
- "Transformational partnership"
- "Best-in-class solutions"
```

```markdown
✅ USE:
- "2,500+ fraud agents across 10 locations supporting 7 clients"
- "WER below 7%, BLEU above 0.70"
- "API-based integration; typical go-live 6-8 weeks"
- "20-year partnership across 7 geographies"
- "Zero CFPB-cited violations across 14M interactions"
```

### DO: Distinguish Claim Types

**Needs Source** (flag if missing):
- Statistics: "99.2% accuracy"
- Metrics: "reduced AHT by 23%"
- Comparatives: "industry-leading"
- Outcomes: "achieved $47M in recoveries"
- Client specifics: "supporting 4 of top 10 banks"

**No Source Needed**:
- Narrative framing: "In today's competitive landscape..."
- Logical transitions: "This approach enables..."
- General principles: "Compliance is essential for..."
- Value propositions: "Our solution will help you..."

### DO: Follow Priority Hierarchy

1. **User Instructions** - Always highest priority
2. **Style Guide** - Foundever RFP style guide principles
3. **Qdrant Database** - 600K+ claims with proof tiers
4. **External Research** - Only when Qdrant lacks coverage

### DON'T: Skip Validation Steps

```markdown
✅ CORRECT WORKFLOW:
1. Call get_research_guidelines FIRST
2. Call check_qdrant_coverage before external search
3. Use validate_claim for key assertions
4. Call check_content_compliance before delivery
5. Run llm_fact_check as final gate
```

### DO: Use Consistent Placeholder Format

```markdown
✅ CORRECT:
{{X delivery centers}}
{{X%}}
{{X,XXX agents}}
{{City, State}}
{{metric: description of what's needed}}
```

```markdown
❌ WRONG:
X delivery centers (no braces)
{X%} (single braces)
{{$X.XM}} (dollar amounts forbidden)
```

---

## Configuration

### Database Configuration

```python
# PostgreSQL
DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "bpo_enrichment",
    "user": "bpo_user",
    "password": "bpo_secure_password_2025"
}

# Qdrant
QDRANT_HOST = "localhost"
QDRANT_PORT = 6333
CLAIMS_COLLECTION = "claims"      # 600K vectors
CHUNKS_COLLECTION = "unified_chunks"  # 135K vectors
```

### LLM Configuration

```python
# Ollama
OLLAMA_URL = "http://localhost:11434/api/generate"
LLM_MODEL = "gpt-oss:120b-analytics"  # Main model (rarely used)
FACT_CHECK_MODEL = "qwen2.5:32b"      # Fast fact-checking
```

### Embedding Configuration

```python
EMBEDDING_MODEL = "intfloat/e5-mistral-7b-instruct"
EMBEDDING_DIM = 4096
```

### Client Personas

| Key | Display Name | Focus Areas |
|-----|--------------|-------------|
| `paytech` | PayTech Client | Payments, fraud, digital wallet |
| `retail_bank` | Retail Bank Client | Banking, Reg E, collections |
| `card_issuer` | Card Issuer Client | Credit cards, disputes, chargebacks |
| `investment_bank` | Investment Bank Client | Wealth, securities, FINRA |
| `insurance_carrier` | Insurance Carrier Client | Claims, FNOL, policy servicing |
| `mortgage_servicer` | Mortgage Servicer Client | Loss mitigation, RESPA, CFPB |
| `fintech_lender` | FinTech Lender Client | Lending, BNPL, state licensing |
| `collections_agency` | Collections Agency Client | Debt, FDCPA, TCPA |

### Proof Tiers

| Tier | Weight | Description |
|------|--------|-------------|
| T0_marketing | 0.3 | Self-reported marketing claims |
| T1_vendor_artifact | 0.7 | Documented vendor capabilities |
| T2_case_study | 0.85 | Published case studies with outcomes |
| T3_third_party_recognition | 1.0 | Awards, analyst reports, certifications |

---

## Endpoints

| Endpoint | URL |
|----------|-----|
| Local | http://localhost:8420 |
| Tailscale (internal) | http://100.120.219.80:8420 |
| **HTTPS (public)** | https://mcp.riorock.app |
| **MCP Endpoint** | https://mcp.riorock.app/mcp/messages |
| Health Check | https://mcp.riorock.app/health |

### Claude Desktop Configuration

```json
{
  "mcpServers": {
    "style-guide-enrichment": {
      "url": "https://mcp.riorock.app/mcp/messages"
    }
  }
}
```

---

## Testing

### Run Overnight Tests

```bash
cd /home/willard/style_guide_enrichment
python3 overnight_test.py
```

### Check Test Progress

```bash
bash /home/willard/style_guide_enrichment/check_test_progress.sh
```

### Test Results Location

- JSON: `/home/willard/style_guide_enrichment/test_results/LATEST_RESULTS.json`
- Report: `/home/willard/style_guide_enrichment/test_results/OVERNIGHT_TEST_REPORT.md`

---

## Quick Start

```bash
# Start server
cd /home/willard/style_guide_enrichment
python3 mcp_server.py 8420

# Or install as service
./install_service.sh

# Check health
curl http://localhost:8420/health
```

---

*Last updated: 2026-01-25*
*Version: 1.0*
*Overnight Test Results: 98% pass rate (49/50)*
