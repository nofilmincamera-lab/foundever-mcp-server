# Foundever MCP Prompts

This directory contains all system prompts and prompt templates used by the Foundever MCP Server.

## Prompt Files

### Core System Prompts

#### foundever_voice_system.txt
**Purpose:** Main system prompt for the Foundever Voice fine-tuned model
**Used by:** `src/config.py` (FOUNDEVER_VOICE_SYSTEM_PROMPT)
**Model:** foundever-voice:latest (Qwen2.5-32B fine-tuned)

Defines the core Foundever RFP writing voice patterns:
- Confirmation syntax
- Value bridges
- So-what closes
- Placeholder usage

#### fact_check_system.txt
**Purpose:** System prompt for rigorous fact-checking of proposal content
**Used by:** `src/config.py` (FACT_CHECK_SYSTEM_PROMPT)
**Model:** qwen2.5:32b

Identifies fabricated statistics, pricing violations, unsourced claims, and style violations.

#### fact_check_user.txt
**Purpose:** User prompt template for fact-checking operations
**Used by:** `src/config.py` (FACT_CHECK_USER_PROMPT)
**Variables:** `{content}`, `{evidence}`

Used to review content against actual evidence found in Qdrant.

### Generation Prompts

#### proposal_generation.txt
**Purpose:** Generate RFP proposal sections from scenarios
**Used by:** `src/overnight_test.py`, testing workflows
**Variables:** `{persona}`, `{scenario}`

Enforces strict rules about placeholders, source attribution, and structure.

#### voice_conversion.txt
**Purpose:** Convert marketing language to practitioner voice
**Used by:** `src/enrichment_engine.py`, `convert_to_practitioner_voice` tool
**Variables:** `{persona}`, `{marketing_phrase}`, `{claims}`

Uses evidence claims to transform marketing phrases into specific, sourced statements.

#### claim_enrichment.txt
**Purpose:** Enrich proposal sections with evidence claims
**Used by:** `src/enrichment_engine.py`, `enrich_section` tool
**Variables:** `{topic}`, `{claims}`

Generates professional sections backed by evidence from Qdrant vector database.

## Usage in Code

### Loading Prompts

```python
# In config.py
def load_prompt(prompt_name: str) -> str:
    """Load a prompt from the prompts/ directory."""
    prompt_path = Path(__file__).parent.parent / "prompts" / f"{prompt_name}.txt"
    with open(prompt_path, 'r') as f:
        return f.read()

FOUNDEVER_VOICE_SYSTEM_PROMPT = load_prompt("foundever_voice_system")
FACT_CHECK_SYSTEM_PROMPT = load_prompt("fact_check_system")
FACT_CHECK_USER_PROMPT = load_prompt("fact_check_user")
```

### Using with Variables

```python
# Format prompts with variables
prompt = load_prompt("voice_conversion").format(
    persona="PayTech Client",
    marketing_phrase="industry-leading fraud detection",
    claims="[Claims from Qdrant search]"
)
```

## Prompt Engineering Guidelines

### 1. Placeholders
- Use `{{placeholder}}` for unknown client-specific data
- Never fabricate statistics or metrics
- Examples: `{{X agents}}`, `{{Y%}}`, `{{$X.XM}}`

### 2. Source Attribution
- Every statistic requires `[Source]` citation
- Format: `"95% accuracy [Source: Internal Analysis 2023]"`
- Unsourced claims will be flagged by fact-checker

### 3. Voice Patterns
- **Confirmation syntax:** "We understand you require..."
- **Value bridges:** "This enables your team to..."
- **So-what closes:** "The result: [specific benefit]"

### 4. Structure
All proposal sections follow:
1. Framing statement (italics)
2. Key metrics/data table
3. "The Point" section
4. Supporting detail
5. Value statement

## Prompt Versioning

When updating prompts:
1. Test changes with `overnight_test.py`
2. Validate fact-checking accuracy
3. Check voice alignment with sample outputs
4. Document changes in this README

## Related Documentation

- [Style Guide](../docs/DOCUMENTATION.md#style-guide) - Full Foundever writing standards
- [MCP Tools](../docs/TOOLS.md) - How prompts are used in MCP tools
- [Training Data](../models/README.md) - How prompts informed model training
