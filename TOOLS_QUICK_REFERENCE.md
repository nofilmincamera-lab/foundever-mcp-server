# Foundever MCP Tools - Quick Reference

**33 Tools organized by category**

---

## 🔍 Core Search Tools (4)

| Tool | Line | Purpose | Calls Prompt? |
|------|------|---------|---------------|
| `search_claims` | 1038 | Semantic search 600K+ claims | ❌ No |
| `search_by_persona` | 1053 | Persona-tailored search | ❌ No |
| `enrich_section` | 1077 | Comprehensive section enrichment | ⚠️ Optional (`claim_enrichment`*) |
| `convert_to_practitioner_voice` | 1118 | Marketing → practitioner | ⚠️ Optional (`voice_conversion`*) |

*Currently inline, not loaded from file

---

## 📘 Style Guide Tools (6)

| Tool | Line | Purpose | Calls Prompt? |
|------|------|---------|---------------|
| `get_style_guide` | 1215 | Complete Foundever style guide | ❌ No (config data) |
| `get_narrative_templates` | 1309 | Narrative patterns | ❌ No (config data) |
| `check_voice` | 1326 | Analyze marketing vs practitioner | ❌ No (regex) |
| `build_section` | 1480 | Generate structured section | ❌ No |
| `get_response_template` | 2656 | Section templates | ❌ No (config data) |
| `search_style_patterns` | 2902 | Query PostgreSQL for patterns | ❌ No |

---

## 🔬 Research & Validation Tools (8)

| Tool | Line | Purpose | Calls Prompt? |
|------|------|---------|---------------|
| `get_research_guidelines` | 1545 | **CRITICAL** - Research protocol | ❌ No (config data) |
| `validate_claim` | 1648 | Validate against Qdrant | ❌ No |
| `check_qdrant_coverage` | 1832 | Check existing evidence | ❌ No |
| `format_sourced_content` | 1915 | Add [Source] attribution | ❌ No |
| `check_content_compliance` | 1958 | Scan for violations | ❌ No (regex) |
| `get_solution_options` | 1719 | Generate 2-3 options | ❌ No |
| `get_foundever_evidence` | 1146 | Foundever evidence package | ❌ No |
| `get_outcome_based_pricing_framing` | 2073 | Pricing talking points | ❌ No (config data) |

---

## 🚫 No-Fabrication Tools (4)

| Tool | Line | Purpose | Calls Prompt? |
|------|------|---------|---------------|
| `get_no_fabrication_policy` | 2124 | No-fabrication rules | ❌ No (config data) |
| `generate_iteration_request` | 2177 | Request missing info | ❌ No |
| `check_for_fabrication` | 2227 | Scan for fabrications | ❌ No (regex) |
| `llm_fact_check` | 2825 | **LLM fact-checking** | ✅ Yes (`fact_check_system`, `fact_check_user`) |

---

## 📄 RFP Input Tools (8)

| Tool | Line | Purpose | Calls Prompt? |
|------|------|---------|---------------|
| `parse_rfp_requirements` | 2324 | Parse RFP documents | ❌ No |
| `generate_clarifying_questions` | 2405 | Generate questions | ❌ No |
| `map_to_style_guide_structure` | 2504 | Map to proposal structure | ❌ No |
| `track_assumptions` | 2608 | Log assumptions | ❌ No |
| *Document parsing tools* | — | Word/Excel/PDF parsing | ❌ No |

---

## 💰 Financial Services Tools (3)

| Tool | Line | Purpose | Calls Prompt? |
|------|------|---------|---------------|
| `get_finserv_persona` | 1371 | FinServ persona details | ❌ No (config data) |
| `get_threat_context` | 1399 | Threat descriptions | ❌ No (config data) |
| `get_finserv_metrics` | 1464 | FinServ metrics | ❌ No (config data) |

---

## ✨ Generation Tools (1)

| Tool | Line | Purpose | Calls Prompt? |
|------|------|---------|---------------|
| `generate_rfp_response` | 3028 | **Generate RFP section** | ✅ Yes (`foundever_voice_system`) |

---

## Prompt Usage Summary

### ✅ Prompts Loaded from Files

| Prompt File | Loaded At | Used By Tool | Model |
|-------------|-----------|--------------|-------|
| `foundever_voice_system.txt` | config.py:69 | `generate_rfp_response` | foundever-voice:latest |
| `fact_check_system.txt` | config.py:72 | `llm_fact_check` | qwen2.5:32b |
| `fact_check_user.txt` | config.py:73 | `llm_fact_check` | qwen2.5:32b |

### ⚠️ Prompts NOT Loaded (Inline in Code)

| Prompt File | Should Be Used In | Currently At |
|-------------|-------------------|--------------|
| `proposal_generation.txt` | Testing only | overnight_test.py:112 |
| `voice_conversion.txt` | `convert_to_practitioner_voice` | enrichment_engine.py:386 |
| `claim_enrichment.txt` | `enrich_section` | enrichment_engine.py:309 |

---

## Tool Statistics

- **Total Tools:** 33
- **Tools Calling LLM:** 2 (6%)
  - `llm_fact_check` (qwen2.5:32b)
  - `generate_rfp_response` (foundever-voice:latest)
- **Tools Using Prompts:** 2 (6%)
  - Both use externalized prompt files
- **Search-Based Tools:** 7 (21%)
- **Config-Based Tools:** 13 (39%)
- **Regex/Rule-Based Tools:** 11 (33%)

---

## Quick Lookup by Line Number

```
1038  search_claims
1053  search_by_persona
1077  enrich_section
1118  convert_to_practitioner_voice
1146  get_foundever_evidence
1215  get_style_guide
1309  get_narrative_templates
1326  check_voice
1371  get_finserv_persona
1399  get_threat_context
1464  get_finserv_metrics
1480  build_section
1545  get_research_guidelines ⚠️ CRITICAL
1648  validate_claim
1719  get_solution_options
1832  check_qdrant_coverage
1915  format_sourced_content
1958  check_content_compliance
2073  get_outcome_based_pricing_framing
2124  get_no_fabrication_policy
2177  generate_iteration_request
2227  check_for_fabrication
2324  parse_rfp_requirements
2405  generate_clarifying_questions
2504  map_to_style_guide_structure
2608  track_assumptions
2656  get_response_template
2825  llm_fact_check 🔥 LLM + PROMPTS
2902  search_style_patterns
3028  generate_rfp_response 🔥 LLM + PROMPTS
```

---

## Common Workflows

### 1. Evidence Search → Validate → Format
```
search_claims → validate_claim → format_sourced_content
```

### 2. Generate → Fact-Check → Iterate
```
generate_rfp_response → llm_fact_check → generate_iteration_request (if needed)
```

### 3. Research → Check Coverage → Search → Enrich
```
get_research_guidelines → check_qdrant_coverage → search_claims → enrich_section
```

### 4. Parse RFP → Map Structure → Generate Sections
```
parse_rfp_requirements → map_to_style_guide_structure → generate_rfp_response (per section)
```

---

**Last Updated:** February 5, 2026
