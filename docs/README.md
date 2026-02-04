# Style Guide Enrichment MCP Server

Semantic search and enrichment tools for Foundever RFP style guides, powered by Qdrant vector database.

> **Full Documentation**: See [DOCUMENTATION.md](DOCUMENTATION.md) for complete technical reference including LLM prompts, architecture, and dos/don'ts.

## Quick Start

```bash
# Start server
cd /home/willard/style_guide_enrichment
python3 mcp_server.py 8420

# Or install as service
./install_service.sh
```

## Endpoints

| Endpoint | URL |
|----------|-----|
| Local | http://localhost:8420 |
| Tailscale (internal) | http://100.120.219.80:8420 |
| **HTTPS (public)** | https://mcp.riorock.app |
| **MCP Endpoint** | https://mcp.riorock.app/mcp/messages |
| Health | https://mcp.riorock.app/health |
| Fallback | https://pop-os-1.tail561ea8.ts.net |

## Claude Desktop Configuration

Add to `~/.config/claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "style-guide-enrichment": {
      "url": "https://mcp.riorock.app/mcp/messages"
    }
  }
}
```

A copy of this config is at: `/home/willard/style_guide_enrichment/claude_desktop_config.json`

**DNS Check:** Run `/home/willard/style_guide_enrichment/check_dns.sh` to verify propagation.

## Available Tools (33 Total)

### Qdrant Search Tools

#### 1. `search_claims`
Semantic search across 600K+ claims in the BPO enrichment database.

```
Query: "collections debt recovery performance"
Filters: domain, provider, proof_tier
Returns: Claims with scores, proof tiers, sources
```

#### 2. `search_by_persona`
Search tailored to client personas (no actual client names used).

**Personas:**
- `paytech` - PayTech Client (digital payments)
- `retail_bank` - Retail Bank Client
- `card_issuer` - Card Issuer Client
- `investment_bank` - Investment Bank Client
- `insurance_carrier` - Insurance Carrier Client
- `mortgage_servicer` - Mortgage Servicer Client
- `fintech_lender` - FinTech Lender Client
- `collections_agency` - Collections Agency Client

#### 3. `enrich_section`
Enrich a style guide section with evidence.

```
Input: "collections debt recovery"
Returns:
- Persona-specific examples
- Discovered metrics
- Taxonomy enrichments
- Foundever-specific patterns
```

#### 4. `convert_to_practitioner_voice`
Convert marketing phrases to practitioner voice using evidence.

```
Input: "world-class fraud prevention capabilities"
Returns: Specific, metric-backed alternatives
```

#### 5. `get_foundever_evidence`
Comprehensive evidence package for Foundever.

#### 6. `get_taxonomy`
Buyer domain taxonomy with definitions.

#### 7. `get_personas`
All available client personas with details.

#### 8. `enrich_taxonomy`
Enrich taxonomy with evidence from database.

### Style Guide Tools

#### 9. `get_style_guide`
Get the complete Foundever RFP Style Guide principles.
- Sections: `all`, `structure`, `voice`, `confidence`, `formatting`, `quality_checklist`
- Includes "1 Plus" structure pattern, practitioner voice guidance, confidence spectrum

#### 10. `get_narrative_templates`
Get narrative pattern templates for RFP writing.
- Categories: `value_bridge`, `risk_mitigation`, `proof_point`, `capability_statement`, `cost_transparency`
- Templates have {{Variable}} placeholders for customization

#### 11. `check_voice`
Analyze text for marketing vs practitioner voice.
- Flags AI-sounding and marketing language
- Suggests practitioner alternatives from the database

#### 12. `get_finserv_persona`
Get detailed Financial Services client persona information.
- 12 persona types: `top_10_retail_bank`, `national_card_issuer`, `regional_credit_union`, etc.
- Returns needs, service types, recommended value statements

#### 13. `get_threat_context`
Get threat/context descriptions for FinServ proposals.
- `app_fraud` - Authorized Push Payment Fraud ($485M)
- `reg_e_surge` - Reg E Dispute Surge Post-Breach
- `cfpb_enforcement` - CFPB Enforcement Environment ($3.7B)
- `deepfakes` - Deepfakes & Synthetic Identity (900% growth)

#### 14. `get_phrases`
Get approved and forbidden phrases for RFP writing.
- Type: `use`, `avoid`, `both`

#### 15. `get_anti_patterns`
Get anti-patterns to avoid in Financial Services RFPs.
- `regulatory_name_dropping` - listing acronyms without substance
- `vague_technology_claims` - unprovable AI/tech claims
- `overpromising_transitions` - "seamless" transitions
- `hiding_pricing` - burying costs in appendices

#### 16. `get_finserv_metrics`
Get Financial Services metrics that matter.
- Categories: `regulatory`, `fraud`, `collections`, `servicing`, `compliance`, `operational`, `financial`

#### 17. `build_section`
Generate a properly structured proposal section using the style guide template.
- Combines evidence from Qdrant with approved section architecture
- Parameters: `topic`, `persona`, `include_evidence`

### Research Guidance Tools (CRITICAL for Deep Research integration)

#### 18. `get_research_guidelines` ⚠️ CALL FIRST
**CRITICAL: Call this BEFORE any research task.**
Returns the research protocol that MUST be followed:
- Priority hierarchy: User → Style Guide → Qdrant → External
- Validation rules (no assumptions, all claims sourced)
- Solution approach (iterate options, don't prescribe)
- When to use Qdrant vs external research

#### 19. `validate_claim`
Validate a claim against Qdrant and return confidence level:
- `VALIDATED`: T2+ evidence
- `SUPPORTED`: T1 evidence or multiple T0
- `INFERRED`: Logical conclusion
- `UNVALIDATED`: Needs confirmation
- `MISSING`: No evidence found

#### 20. `get_solution_options`
Generate 2-3 solution options instead of a single prescription.
Returns options with tradeoffs, dependencies, and clarifying questions.
**Use this to iterate with users.**

#### 21. `check_qdrant_coverage`
Check Qdrant coverage BEFORE doing external research.
Returns:
- Evidence count by proof tier
- Sample claims
- Recommendation: Qdrant only / supplement / external needed
**Prevents redundant Foundever.com searches.**

#### 22. `format_sourced_content`
Format content with proper source attribution.
Ensures every claim has `[Source]` attribution per research guidelines.

#### 23. `check_content_compliance` ⚠️ RUN BEFORE USING CONTENT
Scans content for:
- **PRICING VIOLATIONS** - Any rates, costs, prices (FORBIDDEN)
- **UNSOURCED STATISTICS** - Numbers without `[Source]` attribution

Returns issues that MUST be fixed before content is used.

#### 24. `get_outcome_based_pricing_framing`
The ONLY pricing topic allowed. Returns:
- Approved talking points for outcome-based models
- How to position value-based arrangements
- Questions to iterate with user on commercial models

### No-Fabrication Tools (CRITICAL)

#### 25. `get_no_fabrication_policy` ⛔
Returns the strict no-fabrication rules:
- What counts as fabrication (NEVER DO)
- How to use `{{placeholders}}` correctly
- How to iterate with user for real facts

**Goal: Build narrative → Placeholder facts → Iterate with user**

#### 26. `generate_iteration_request`
Generate a structured request for missing information:
- Lists what verified data is needed
- Provides placeholder format
- Offers options to user (provide data / keep placeholders / rescope)

**Use this instead of making up data.**

#### 27. `check_for_fabrication`
Scan content for potentially fabricated information:
- Specific numbers without `[Source]` attribution
- Round numbers that look estimated
- Precise figures that weren't in search results

Returns list of suspected fabrications to fix.

#### 28. `llm_fact_check` 🤖 FINAL PASS
Uses local LLM (qwen2.5:32b) for rigorous fact-checking.

The LLM will:
1. Identify fabricated statistics
2. Flag unsourced claims
3. Detect pricing violations
4. Verify proper attribution
5. Return PASS/FAIL recommendation

**Use as final quality gate before content delivery.**

Note: Takes ~10-30 seconds (uses faster 32B model, not 120B).

### RFP Input Handling Tools

#### 29. `parse_rfp_requirements`
Parse requirements from client documents (Word, Excel, PDF).
- Extracts discrete requirements
- Categorizes by section
- Flags gaps (timeline, volume, geography, etc.)
- Identifies questions to answer

#### 30. `generate_clarifying_questions`
Generate questions for ambiguous requirements:
- Scope & Volume questions
- Timeline & Implementation
- Geography & Languages
- Technology & Integration
- Regulatory & Compliance
- Success Metrics
- Commercial Model

**Ask these BEFORE drafting - don't assume.**

#### 31. `map_to_style_guide_structure`
Map RFP requirements to standard proposal sections:
1. Executive Summary (1 Plus structure)
2. Understanding Client Needs
3. Solution Overview
4. Delivery Model
5. Technology & Innovation
6. Governance & Compliance
7. Implementation & Transition
8. Team & Leadership
9. Proof Points & Evidence

Returns section-by-section outline.

#### 32. `track_assumptions`
Track assumptions needing user confirmation:
- Log assumptions being made
- Show impact if wrong
- Define default behavior
- Require explicit confirmation

**Never proceed with unconfirmed assumptions.**

#### 33. `get_response_template`
Get style-guide-compliant section templates:
- Proper header format
- Metrics table structure
- "The Point" section
- Evidence placement
- Value statement format

Templates for: executive_summary, solution_overview, delivery_model, governance_compliance, implementation, etc.

## Buyer Domains

| Domain | Description |
|--------|-------------|
| Customer Experience Operations | Inbound/outbound service, support |
| Collections & Revenue Recovery | First/third-party collections |
| Financial Crime & Compliance | Fraud, AML, KYC, compliance |
| Sales Operations | Outbound sales, lead qualification |
| Finance & Accounting Operations | Back-office finance, reconciliation |
| Tech Support Operations | Technical support, help desk |
| Trust & Safety Operations | Content moderation, account safety |

## Proof Tiers

| Tier | Weight | Description |
|------|--------|-------------|
| T0_marketing | 0.3 | Marketing claims |
| T1_vendor_artifact | 0.7 | Documented vendor capabilities |
| T2_case_study | 0.85 | Case study evidence |
| T3_third_party_recognition | 1.0 | Awards, analyst reports |

## CLI Usage

```bash
# Enrich a section
python main.py --section "collections debt recovery"

# Foundever analysis
python main.py --foundever-analysis

# Convert marketing voice
python main.py --convert "world-class fraud prevention"

# Persona search
python main.py --persona card_issuer --query "dispute resolution"

# Output as JSON
python main.py --section "fraud" --json
```

## Architecture

```
┌─────────────────────────────────────────────────┐
│  Claude / MCP Client                            │
│  http://riorock.app:8420/mcp/messages           │
└─────────────────┬───────────────────────────────┘
                  │ SSE
┌─────────────────▼───────────────────────────────┐
│  MCP Server (mcp_server.py)                     │
│  - Tool definitions                             │
│  - Request handling                             │
└─────────────────┬───────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────┐
│  Enrichment Engine (enrichment_engine.py)       │
│  - Section enrichment                           │
│  - Voice conversion                             │
│  - Taxonomy enrichment                          │
└─────────────────┬───────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────┐
│  Semantic Search (search.py)                    │
│  - Claims search (4096-dim)                     │
│  - Chunks search (2048-dim)                     │
│  - Persona-based filtering                      │
└─────────────────┬───────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────┐
│  Embedder (embedder.py)                         │
│  intfloat/e5-mistral-7b-instruct                │
└─────────────────┬───────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────┐
│  Qdrant (localhost:6333)                        │
│  - claims: 600K vectors (4096-dim)              │
│  - unified_chunks: 135K vectors (2048-dim)      │
└─────────────────────────────────────────────────┘
```

## Files

| File | Purpose |
|------|---------|
| `config.py` | Configuration, personas, taxonomy |
| `embedder.py` | E5-Mistral embedding generation |
| `search.py` | Qdrant semantic search |
| `enrichment_engine.py` | Style guide enrichment |
| `main.py` | CLI interface |
| `mcp_server.py` | MCP HTTP/SSE server |

## Dependencies

- Python 3.10+
- PyTorch with CUDA
- Transformers (intfloat/e5-mistral-7b-instruct)
- Qdrant Client
- MCP SDK
- Starlette + Uvicorn
