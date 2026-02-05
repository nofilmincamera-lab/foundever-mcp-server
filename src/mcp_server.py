#!/usr/bin/env python3
"""
Style Guide Enrichment MCP Server
==================================
Model Context Protocol server for Claude integration.
Exposes style guide enrichment tools via HTTP/SSE.

Endpoint: http://riorock.app:8420/mcp (or Tailscale IP)
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional
from dataclasses import asdict
from contextlib import asynccontextmanager

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.server.sse import SseServerTransport
from mcp.types import (
    Tool,
    TextContent,
    CallToolResult,
    ListToolsResult,
)
from starlette.applications import Starlette
from starlette.routing import Route
from starlette.responses import JSONResponse
import uvicorn

# Import our enrichment modules
from config import (
    CLIENT_PERSONAS, BUYER_DOMAIN_TAXONOMY, PROOF_TIERS,
    FINSERV_PERSONAS, VOICE_CONVERSIONS, NARRATIVE_TEMPLATES,
    PERSONA_VALUE_STATEMENTS, THREAT_CONTEXTS, PHRASES_TO_USE,
    PHRASES_TO_AVOID, FINSERV_METRICS, ANTI_PATTERNS,
    SECTION_TEMPLATE, ONE_PLUS_STRUCTURE,
    RESEARCH_GUIDELINES, RESEARCH_MODE_HEADER, CLAIM_CONFIDENCE,
    OLLAMA_URL, FACT_CHECK_MODEL, FACT_CHECK_SYSTEM_PROMPT, FACT_CHECK_USER_PROMPT,
    FOUNDEVER_VOICE_MODEL, FOUNDEVER_VOICE_SYSTEM_PROMPT
)
from search import get_searcher, SearchResult
from enrichment_engine import get_enricher
from document_tools import DOCUMENT_TOOLS, handle_document_tool
import re
import httpx
import psycopg2
from config import DB_CONFIG

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mcp-style-guide")

# Global instances (pre-loaded at startup)
_searcher = None
_enricher = None


def init_models():
    """
    Pre-load all models at server startup.

    This ensures the first tool call is fast by loading:
    - Embedder (E5-Mistral-7B): ~7-14 GB, 10-30 seconds
    - Searcher (Qdrant client): ~50 MB, 0.5 seconds
    - Enricher: ~10 MB, 0.1 seconds

    Total startup time: ~10-30 seconds
    Total memory: ~7-14 GB
    """
    global _searcher, _enricher

    logger.info("=" * 60)
    logger.info("PRE-LOADING MODELS AT STARTUP")
    logger.info("=" * 60)

    # Load Searcher (which also loads Embedder)
    logger.info("Loading Searcher + Embedder...")
    logger.info("  → E5-Mistral-7B (7-14 GB, ~10-30s)")
    logger.info("  → Qdrant Client (~50 MB, ~0.5s)")
    _searcher = get_searcher()
    logger.info("✓ Searcher + Embedder loaded successfully")

    # Load Enricher
    logger.info("Loading Enricher...")
    logger.info("  → Enrichment Engine (~10 MB, ~0.1s)")
    _enricher = get_enricher(use_llm=False)
    logger.info("✓ Enricher loaded successfully")

    logger.info("=" * 60)
    logger.info("ALL MODELS PRE-LOADED - SERVER READY")
    logger.info("=" * 60)


def get_lazy_searcher():
    """Get searcher instance (pre-loaded at startup, so always available)."""
    global _searcher
    if _searcher is None:
        logger.warning("Searcher not pre-loaded! Loading now...")
        _searcher = get_searcher()
    return _searcher


def get_lazy_enricher(use_llm: bool = False):
    """Get enricher instance (pre-loaded at startup, so always available)."""
    global _enricher
    if _enricher is None:
        logger.warning("Enricher not pre-loaded! Loading now...")
        _enricher = get_enricher(use_llm=use_llm)
    return _enricher


# Define MCP Tools
TOOLS = [
    Tool(
        name="search_claims",
        description="""Search the BPO enrichment claims database using semantic similarity.

Returns claims with proof tiers (T0_marketing, T1_vendor_artifact, T2_case_study, T3_third_party_recognition).
Use this to find evidence for RFP responses, validate capabilities, or gather metrics.""",
        inputSchema={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Semantic search query (e.g., 'collections debt recovery performance')"
                },
                "domain": {
                    "type": "string",
                    "description": "Filter by buyer domain",
                    "enum": list(BUYER_DOMAIN_TAXONOMY.keys())
                },
                "provider": {
                    "type": "string",
                    "description": "Filter by provider name (e.g., 'Foundever')"
                },
                "proof_tier": {
                    "type": "string",
                    "description": "Filter by proof tier",
                    "enum": list(PROOF_TIERS.keys())
                },
                "limit": {
                    "type": "integer",
                    "description": "Max results (default: 10)",
                    "default": 10
                }
            },
            "required": ["query"]
        }
    ),
    Tool(
        name="search_by_persona",
        description="""Search evidence tailored to a specific client persona.

Personas are variable-based templates (not actual client names):
- paytech: PayTech Client (digital payments)
- retail_bank: Retail Bank Client
- card_issuer: Card Issuer Client
- investment_bank: Investment Bank Client
- insurance_carrier: Insurance Carrier Client
- mortgage_servicer: Mortgage Servicer Client
- fintech_lender: FinTech Lender Client
- collections_agency: Collections Agency Client""",
        inputSchema={
            "type": "object",
            "properties": {
                "persona": {
                    "type": "string",
                    "description": "Client persona key",
                    "enum": list(CLIENT_PERSONAS.keys())
                },
                "query": {
                    "type": "string",
                    "description": "Search query"
                },
                "limit": {
                    "type": "integer",
                    "description": "Max results per domain (default: 5)",
                    "default": 5
                }
            },
            "required": ["persona", "query"]
        }
    ),
    Tool(
        name="enrich_section",
        description="""Enrich a style guide section with evidence from the database.

Returns:
- Persona-specific examples
- Discovered metrics
- Taxonomy enrichments
- Foundever-specific patterns
- Generated templates (if LLM enabled)""",
        inputSchema={
            "type": "object",
            "properties": {
                "section_topic": {
                    "type": "string",
                    "description": "Topic of the section to enrich (e.g., 'collections debt recovery')"
                },
                "personas": {
                    "type": "array",
                    "items": {"type": "string", "enum": list(CLIENT_PERSONAS.keys())},
                    "description": "Personas to generate examples for",
                    "default": ["paytech", "retail_bank", "card_issuer"]
                },
                "use_llm": {
                    "type": "boolean",
                    "description": "Use LLM for template generation (slower)",
                    "default": False
                }
            },
            "required": ["section_topic"]
        }
    ),
    Tool(
        name="convert_to_practitioner_voice",
        description="""Convert marketing phrases to practitioner voice using evidence.

Takes generic marketing language and finds specific, metric-backed alternatives from the database.
Essential for following the style guide principle: 'Write like a practitioner, not a marketer.'""",
        inputSchema={
            "type": "object",
            "properties": {
                "marketing_phrase": {
                    "type": "string",
                    "description": "Marketing phrase to convert (e.g., 'world-class fraud prevention')"
                },
                "domain": {
                    "type": "string",
                    "description": "Target buyer domain",
                    "enum": list(BUYER_DOMAIN_TAXONOMY.keys()),
                    "default": "Customer Experience Operations"
                },
                "persona": {
                    "type": "string",
                    "description": "Target client persona",
                    "enum": list(CLIENT_PERSONAS.keys()),
                    "default": "retail_bank"
                },
                "count": {
                    "type": "integer",
                    "description": "Number of alternatives (default: 3)",
                    "default": 3
                }
            },
            "required": ["marketing_phrase"]
        }
    ),
    Tool(
        name="get_foundever_evidence",
        description="""Get comprehensive evidence package for Foundever.

Returns:
- Total claims count
- Distribution by proof tier
- Distribution by buyer domain
- Top outcomes (T1+/T2)
- Case studies""",
        inputSchema={
            "type": "object",
            "properties": {
                "domains": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Filter by specific buyer domains (optional)"
                }
            }
        }
    ),
    Tool(
        name="get_taxonomy",
        description="""Get the buyer domain taxonomy with definitions.

Returns all buyer domains with:
- Description
- Sub-functions
- Standard metrics""",
        inputSchema={
            "type": "object",
            "properties": {}
        }
    ),
    Tool(
        name="get_personas",
        description="""Get all available client personas with details.

Returns persona definitions including:
- Display name
- Description
- Relevant domains
- Keywords
- Regulatory focus areas""",
        inputSchema={
            "type": "object",
            "properties": {}
        }
    ),
    Tool(
        name="enrich_taxonomy",
        description="""Enrich the entire buyer domain taxonomy with evidence.

For each domain, discovers:
- New metrics from evidence
- Capabilities
- Example claims
- Evidence count""",
        inputSchema={
            "type": "object",
            "properties": {
                "provider": {
                    "type": "string",
                    "description": "Provider to get evidence from",
                    "default": "Foundever"
                }
            }
        }
    ),
    # ========== STYLE GUIDE TOOLS ==========
    Tool(
        name="get_style_guide",
        description="""Get the complete Foundever RFP Style Guide principles.

Returns writing guidelines including:
- The "1 Plus" Structure pattern
- Practitioner vs Marketing voice guidance
- Confidence spectrum for claims
- Section architecture templates
- Language and tone rules""",
        inputSchema={
            "type": "object",
            "properties": {
                "section": {
                    "type": "string",
                    "description": "Specific section to retrieve",
                    "enum": ["all", "structure", "voice", "confidence", "formatting", "quality_checklist"]
                }
            }
        }
    ),
    Tool(
        name="get_narrative_templates",
        description="""Get narrative pattern templates for RFP writing.

Template categories:
- value_bridge: Connect delivery components to client outcomes
- risk_mitigation: Address client concerns proactively
- proof_point: Substantiate claims with evidence
- capability_statement: Articulate operational strengths
- cost_transparency: Present pricing clearly

Each template has placeholders like {{Variable}} for customization.""",
        inputSchema={
            "type": "object",
            "properties": {
                "category": {
                    "type": "string",
                    "description": "Template category to retrieve",
                    "enum": ["value_bridge", "risk_mitigation", "proof_point", "capability_statement", "cost_transparency", "all"]
                }
            },
            "required": ["category"]
        }
    ),
    Tool(
        name="check_voice",
        description="""Analyze text for marketing vs practitioner voice.

Flags AI-sounding and marketing language, then suggests practitioner alternatives.
Use this to convert generic claims into specific, metric-backed statements.""",
        inputSchema={
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "The text to analyze for voice issues"
                },
                "suggest_alternatives": {
                    "type": "boolean",
                    "description": "Include alternative phrasings from the database",
                    "default": True
                }
            },
            "required": ["text"]
        }
    ),
    Tool(
        name="get_finserv_persona",
        description="""Get detailed information about a Financial Services client persona.

Returns persona description, typical needs, service types, and recommended value statements.
Use for tailoring proposals to specific client types.""",
        inputSchema={
            "type": "object",
            "properties": {
                "persona": {
                    "type": "string",
                    "description": "Persona key",
                    "enum": list(FINSERV_PERSONAS.keys())
                }
            },
            "required": ["persona"]
        }
    ),
    Tool(
        name="get_threat_context",
        description="""Get threat/context descriptions for Financial Services proposals.

Provides statistics, context, and commitment statements for:
- Authorized Push Payment (APP) Fraud
- Reg E Dispute Surge Post-Breach
- CFPB Enforcement Environment
- Deepfakes & Synthetic Identity

Use to establish stakes without fear-mongering.""",
        inputSchema={
            "type": "object",
            "properties": {
                "threat": {
                    "type": "string",
                    "description": "Threat context to retrieve",
                    "enum": list(THREAT_CONTEXTS.keys()) + ["all"]
                }
            },
            "required": ["threat"]
        }
    ),
    Tool(
        name="get_phrases",
        description="""Get approved and forbidden phrases for RFP writing.

Returns:
- Phrases to use (with context)
- Phrases to avoid (with explanations)

Use to ensure consistent, effective language across proposals.""",
        inputSchema={
            "type": "object",
            "properties": {
                "type": {
                    "type": "string",
                    "description": "Which phrases to retrieve",
                    "enum": ["use", "avoid", "both"]
                }
            }
        }
    ),
    Tool(
        name="get_anti_patterns",
        description="""Get anti-patterns to avoid in Financial Services RFPs.

Each anti-pattern includes:
- Bad example (what NOT to do)
- Good example (what TO do)
- Explanation of why

Categories: regulatory_name_dropping, vague_technology_claims, overpromising_transitions, hiding_pricing""",
        inputSchema={
            "type": "object",
            "properties": {
                "pattern": {
                    "type": "string",
                    "description": "Specific anti-pattern",
                    "enum": list(ANTI_PATTERNS.keys()) + ["all"]
                }
            }
        }
    ),
    Tool(
        name="get_finserv_metrics",
        description="""Get Financial Services metrics that matter for proposals.

Categories:
- regulatory: Examination findings, SAR accuracy, complaint ratios
- fraud: Fraud losses (bps), false positive rate
- collections: RPC rate, PTP rate, liquidation rate
- servicing: FCR, AHT, CSAT/NPS
- compliance: QA pass rate, training completion
- operational: Attrition, speed-to-proficiency
- financial: Cost per contact, savings vs. baseline""",
        inputSchema={
            "type": "object",
            "properties": {
                "category": {
                    "type": "string",
                    "description": "Metric category",
                    "enum": list(FINSERV_METRICS.keys()) + ["all"]
                }
            }
        }
    ),
    Tool(
        name="build_section",
        description="""Generate a properly structured proposal section using the style guide template.

Combines evidence from Qdrant with the approved section architecture:
- Framing statement
- Quick-scan metrics
- "The Point" explanation
- Supporting detail
- Value statement for client

Pass in the topic and persona to get a complete section draft.""",
        inputSchema={
            "type": "object",
            "properties": {
                "topic": {
                    "type": "string",
                    "description": "Section topic (e.g., 'collections performance', 'fraud prevention')"
                },
                "persona": {
                    "type": "string",
                    "description": "Target client persona",
                    "enum": list(FINSERV_PERSONAS.keys())
                },
                "include_evidence": {
                    "type": "boolean",
                    "description": "Include evidence from Qdrant database",
                    "default": True
                }
            },
            "required": ["topic", "persona"]
        }
    ),
    # ========== RESEARCH GUIDANCE TOOLS ==========
    Tool(
        name="get_research_guidelines",
        description="""CRITICAL: Call this FIRST before any research task.

Returns the research protocol that MUST be followed:
- Priority hierarchy: User → Style Guide → Qdrant → External
- Validation rules (no assumptions, all claims sourced)
- Solution approach (iterate options, don't prescribe)
- When to use Qdrant vs external research
- Claim attribution format

This ensures research is disciplined, traceable, and non-redundant.""",
        inputSchema={
            "type": "object",
            "properties": {
                "section": {
                    "type": "string",
                    "description": "Specific section to retrieve",
                    "enum": ["all", "priority", "validation", "solution_approach", "qdrant_vs_external", "attribution"]
                }
            }
        }
    ),
    Tool(
        name="validate_claim",
        description="""Validate a claim against the Qdrant database and return confidence level.

Returns:
- VALIDATED: T2+ evidence or user confirmation
- SUPPORTED: T1 evidence or multiple T0 sources
- INFERRED: Logical conclusion from facts
- UNVALIDATED: Needs confirmation
- MISSING: No evidence found

Use this before asserting any fact in proposals.""",
        inputSchema={
            "type": "object",
            "properties": {
                "claim": {
                    "type": "string",
                    "description": "The claim to validate"
                },
                "provider": {
                    "type": "string",
                    "description": "Provider to check (default: Foundever)",
                    "default": "Foundever"
                }
            },
            "required": ["claim"]
        }
    ),
    Tool(
        name="get_solution_options",
        description="""Generate solution options for a client need rather than a single prescription.

Returns 2-3 options with:
- Approach description
- Tradeoffs (pros/challenges)
- Dependencies and assumptions
- Questions to clarify with user

Use this to iterate with users instead of assuming the right solution.""",
        inputSchema={
            "type": "object",
            "properties": {
                "need": {
                    "type": "string",
                    "description": "The client need or problem to address"
                },
                "persona": {
                    "type": "string",
                    "description": "Client persona for context",
                    "enum": list(FINSERV_PERSONAS.keys())
                },
                "constraints": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Known constraints (budget, timeline, regulatory, etc.)"
                }
            },
            "required": ["need", "persona"]
        }
    ),
    Tool(
        name="check_qdrant_coverage",
        description="""Check what Qdrant already has for a topic BEFORE doing external research.

Returns:
- Evidence count by proof tier
- Sample claims with sources
- Gaps that may need external research
- Recommendation: use Qdrant only, supplement with external, or external needed

Prevents redundant external research when Qdrant already has the data.""",
        inputSchema={
            "type": "object",
            "properties": {
                "topic": {
                    "type": "string",
                    "description": "Topic to check coverage for"
                },
                "provider": {
                    "type": "string",
                    "description": "Provider to focus on",
                    "default": "Foundever"
                }
            },
            "required": ["topic"]
        }
    ),
    Tool(
        name="format_sourced_content",
        description="""Format content with proper source attribution.

Takes draft content and evidence, returns properly attributed version.
Ensures every claim has [Source] attribution per research guidelines.""",
        inputSchema={
            "type": "object",
            "properties": {
                "content": {
                    "type": "string",
                    "description": "Draft content to attribute"
                },
                "evidence": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Evidence sources used"
                }
            },
            "required": ["content"]
        }
    ),
    Tool(
        name="check_content_compliance",
        description="""CRITICAL: Check content for pricing violations and unsourced statistics.

Scans content for:
1. PRICING VIOLATIONS - Any mention of rates, costs, prices (FORBIDDEN)
2. UNSOURCED STATISTICS - Numbers without [Source] attribution (MUST FIX)

Returns issues that MUST be fixed before content is used.

Exception: Outcome-based pricing can be discussed as a solution concept.""",
        inputSchema={
            "type": "object",
            "properties": {
                "content": {
                    "type": "string",
                    "description": "Content to check for compliance"
                }
            },
            "required": ["content"]
        }
    ),
    Tool(
        name="get_outcome_based_pricing_framing",
        description="""Get approved framing for outcome-based pricing discussions.

This is the ONLY pricing topic allowed. Returns:
- Approved talking points
- How to position outcome-based models
- Questions to iterate with user

Use when client discussions turn to commercial models.""",
        inputSchema={
            "type": "object",
            "properties": {}
        }
    ),
    Tool(
        name="get_no_fabrication_policy",
        description="""CRITICAL: Get the no-fabrication policy.

Returns rules for handling missing information:
- What counts as fabrication (NEVER DO)
- How to use {{placeholders}} correctly
- How to iterate with user for real facts
- The goal: build narrative, placeholder facts, iterate

Call this when you're tempted to 'fill in' missing data.""",
        inputSchema={
            "type": "object",
            "properties": {}
        }
    ),
    Tool(
        name="generate_iteration_request",
        description="""Generate a structured request for missing information from user.

Instead of fabricating data, use this to:
1. List what verified information is needed
2. Explain why each piece is needed
3. Provide placeholder format for user to fill
4. Offer to continue with placeholders if user prefers

This is the CORRECT approach when data is missing.""",
        inputSchema={
            "type": "object",
            "properties": {
                "section": {
                    "type": "string",
                    "description": "Section or topic being worked on"
                },
                "missing_items": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of specific data points needed"
                },
                "context": {
                    "type": "string",
                    "description": "Why this information is needed"
                }
            },
            "required": ["section", "missing_items"]
        }
    ),
    Tool(
        name="check_for_fabrication",
        description="""Scan content for potentially fabricated information.

Detects:
- Specific numbers without [Source] attribution
- Statistics that look invented (round numbers, precise figures)
- Details that weren't in search results
- Claims that sound authoritative but lack evidence

Returns list of suspected fabrications that should be placeholdered.""",
        inputSchema={
            "type": "object",
            "properties": {
                "content": {
                    "type": "string",
                    "description": "Content to scan for fabrication"
                },
                "search_results_summary": {
                    "type": "string",
                    "description": "Summary of what was actually found in searches (optional)"
                }
            },
            "required": ["content"]
        }
    ),
    Tool(
        name="llm_fact_check",
        description="""FINAL PASS: Use local LLM to fact-check content.

Sends content to qwen2.5:32b running on Ollama for rigorous fact-checking.

The LLM will:
1. Identify fabricated statistics
2. Flag unsourced claims
3. Detect pricing violations
4. Verify proper attribution
5. Return PASS/FAIL recommendation

Use this as the final quality gate before content is delivered.

Note: This calls the local LLM and may take 10-30 seconds.""",
        inputSchema={
            "type": "object",
            "properties": {
                "content": {
                    "type": "string",
                    "description": "Content to fact-check"
                },
                "evidence_summary": {
                    "type": "string",
                    "description": "Summary of evidence that was actually found in Qdrant searches"
                }
            },
            "required": ["content"]
        }
    ),
    # ========== RFP INPUT HANDLING TOOLS ==========
    Tool(
        name="parse_rfp_requirements",
        description="""Parse RFP requirements from client documents.

Takes extracted text from Word/Excel/PDF and:
1. Identifies discrete requirements
2. Categorizes by style guide section
3. Flags ambiguities needing clarification
4. Notes missing critical information

Returns structured requirements with gaps identified.""",
        inputSchema={
            "type": "object",
            "properties": {
                "document_text": {
                    "type": "string",
                    "description": "Extracted text from RFP document"
                },
                "document_type": {
                    "type": "string",
                    "description": "Type of document",
                    "enum": ["word_doc", "excel_questions", "pdf_rfp", "email", "other"]
                },
                "client_persona": {
                    "type": "string",
                    "description": "Client persona if known",
                    "enum": list(FINSERV_PERSONAS.keys()) + ["unknown"]
                }
            },
            "required": ["document_text"]
        }
    ),
    Tool(
        name="generate_clarifying_questions",
        description="""Generate clarifying questions for ambiguous RFP requirements.

Based on parsed requirements, generates questions for:
- Ambiguous scope
- Missing critical info (timeline, volume, geography)
- Conflicting requirements
- Unstated assumptions
- Regulatory implications
- Technical integration gaps
- Undefined success metrics

Returns prioritized questions to ask client/user.""",
        inputSchema={
            "type": "object",
            "properties": {
                "requirements": {
                    "type": "string",
                    "description": "Parsed requirements or raw RFP text"
                },
                "identified_gaps": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Already identified gaps (optional)"
                }
            },
            "required": ["requirements"]
        }
    ),
    Tool(
        name="map_to_style_guide_structure",
        description="""Map RFP requirements to style guide section structure.

Takes requirements and maps them to the standard proposal structure:
1. Executive Summary (1 Plus structure)
2. Understanding Client Needs
3. Solution Overview
4. Delivery Model
5. Technology & Innovation
6. Governance & Compliance
7. Implementation & Transition
8. Team & Leadership
9. Proof Points & Evidence

Returns section-by-section outline with requirements mapped.""",
        inputSchema={
            "type": "object",
            "properties": {
                "requirements": {
                    "type": "string",
                    "description": "Parsed RFP requirements"
                },
                "persona": {
                    "type": "string",
                    "description": "Client persona",
                    "enum": list(FINSERV_PERSONAS.keys())
                }
            },
            "required": ["requirements", "persona"]
        }
    ),
    Tool(
        name="track_assumptions",
        description="""Track assumptions that need user confirmation.

Use this to:
1. Log assumptions being made
2. Generate confirmation requests
3. Track which assumptions are confirmed/rejected
4. Flag assumptions that affect solution design

Returns formatted assumption tracker for user review.""",
        inputSchema={
            "type": "object",
            "properties": {
                "assumptions": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "assumption": {"type": "string"},
                            "impact": {"type": "string"},
                            "default_if_not_confirmed": {"type": "string"}
                        }
                    },
                    "description": "List of assumptions to track"
                },
                "context": {
                    "type": "string",
                    "description": "Context for these assumptions"
                }
            },
            "required": ["assumptions"]
        }
    ),
    Tool(
        name="get_response_template",
        description="""Get a style-guide-compliant response template for a section.

Returns the proper structure including:
- Section header format
- Framing statement placeholder
- Metrics table structure
- "The Point" section
- Evidence placement
- Value statement format

Use this to ensure output follows style guide structure.""",
        inputSchema={
            "type": "object",
            "properties": {
                "section_type": {
                    "type": "string",
                    "description": "Type of section",
                    "enum": [
                        "executive_summary",
                        "client_understanding",
                        "solution_overview",
                        "delivery_model",
                        "technology",
                        "governance_compliance",
                        "implementation",
                        "team_leadership",
                        "proof_points",
                        "pricing_approach"
                    ]
                },
                "persona": {
                    "type": "string",
                    "description": "Client persona",
                    "enum": list(FINSERV_PERSONAS.keys())
                }
            },
            "required": ["section_type"]
        }
    ),
    Tool(
        name="search_style_patterns",
        description="""Search Foundever's voice model patterns for style-consistent generation.

Returns narrative templates extracted from actual RFP responses. Use these as few-shot examples
to ensure generated content matches Foundever's writing style and structure.

Pattern Types:
- confirmation_protocol: How to acknowledge client requirements ("Confirmed. {{Company}} confirms...")
- value_bridge: Connect features to benefits ("{{Feature}} enables {{Client}} to achieve...")
- so_what_close: Summary value statements ("Value for {{Client}}: {{Strategic_Outcome}}")
- visual_frame: Introduce charts/tables ("The following illustrates...")
- spatial_argument: What visuals prove ("This demonstrates...")

Categories: collections, fraud, governance, customer_service, technology, general

Use this tool when generating RFP sections to retrieve relevant style patterns as guidance.""",
        inputSchema={
            "type": "object",
            "properties": {
                "template_type": {
                    "type": "string",
                    "description": "Type of pattern to search for",
                    "enum": ["confirmation_protocol", "value_bridge", "so_what_close", "visual_frame", "spatial_argument"]
                },
                "category": {
                    "type": "string",
                    "description": "Service category filter",
                    "enum": ["collections", "fraud", "governance", "customer_service", "technology", "general"]
                },
                "keyword": {
                    "type": "string",
                    "description": "Optional keyword to search within templates"
                },
                "limit": {
                    "type": "integer",
                    "description": "Max results (default: 10)",
                    "default": 10
                }
            },
            "required": []
        }
    ),
    Tool(
        name="generate_rfp_response",
        description="""Generate an RFP response section using Foundever's fine-tuned voice model.

This tool uses a 32B parameter model fine-tuned on 4,321 Foundever RFP examples to generate
responses in authentic Foundever voice with:
- Confirmation syntax for acknowledging requirements
- Value bridges connecting features to client benefits
- So-what closes summarizing value propositions
- {{placeholders}} for specific client data

Use for: Collections, Financial Services, Customer Service, Fraud, Technology responses.

The model will NOT hallucinate specific facts - it uses placeholders where data should be provided.""",
        inputSchema={
            "type": "object",
            "properties": {
                "requirement": {
                    "type": "string",
                    "description": "The client requirement or RFP question to respond to"
                },
                "context": {
                    "type": "string",
                    "description": "Additional context (e.g., client industry, service type, specific constraints)"
                },
                "section_type": {
                    "type": "string",
                    "description": "Type of RFP section",
                    "enum": ["executive_summary", "solution_approach", "staffing", "technology", "compliance", "pricing_intro", "general"]
                }
            },
            "required": ["requirement"]
        }
    )
]


def format_search_results(results: List[SearchResult]) -> str:
    """Format search results for display."""
    if not results:
        return "No results found."

    output = []
    for i, r in enumerate(results, 1):
        tier_badge = f"[{r.proof_tier}]" if r.proof_tier else "[T0]"
        domain_badge = f"[{r.domain}]" if r.domain else ""
        output.append(f"{i}. {tier_badge} {domain_badge} (score: {r.score:.3f})")
        output.append(f"   Provider: {r.provider}")
        output.append(f"   {r.text[:200]}...")
        if r.source_url:
            output.append(f"   Source: {r.source_url[:60]}...")
        output.append("")

    return "\n".join(output)


async def handle_tool_call(name: str, arguments: Dict[str, Any]) -> str:
    """Handle MCP tool calls."""
    try:
        # Try document tools first
        doc_result = await handle_document_tool(name, arguments)
        if doc_result is not None:
            return doc_result

        if name == "search_claims":
            searcher = get_lazy_searcher()
            results = searcher.search_claims(
                query=arguments["query"],
                limit=arguments.get("limit", 10),
                provider_filter=arguments.get("provider"),
                domain_filter=arguments.get("domain"),
                proof_tier_filter=[arguments["proof_tier"]] if arguments.get("proof_tier") else None
            )
            return format_search_results(results)

        elif name == "search_by_persona":
            searcher = get_lazy_searcher()
            persona_key = arguments["persona"]

            if persona_key not in CLIENT_PERSONAS:
                return f"Unknown persona: {persona_key}. Available: {', '.join(CLIENT_PERSONAS.keys())}"

            results = searcher.search_for_persona(
                persona_key=persona_key,
                query=arguments["query"],
                limit=arguments.get("limit", 5)
            )

            persona = CLIENT_PERSONAS[persona_key]
            output = [f"# Results for {persona['display_name']}", f"_{persona['description']}_", ""]

            for domain, claims in results.items():
                output.append(f"## {domain}")
                for r in claims[:5]:
                    output.append(f"- [{r.proof_tier}] {r.text[:100]}...")
                output.append("")

            return "\n".join(output)

        elif name == "enrich_section":
            enricher = get_lazy_enricher(use_llm=arguments.get("use_llm", False))
            personas = arguments.get("personas", ["paytech", "retail_bank", "card_issuer"])

            enrichment = enricher.enrich_section(
                section_topic=arguments["section_topic"],
                target_personas=personas,
                include_taxonomy=True
            )

            output = [
                f"# Section Enrichment: {enrichment.section_name}",
                f"Generated: {enrichment.timestamp}",
                "",
                "## Evidence Summary",
                f"- High-quality claims: {enrichment.raw_evidence['high_quality_count']}",
                f"- Case study evidence: {enrichment.raw_evidence['case_study_count']}",
                f"- Outcome metrics: {enrichment.raw_evidence['outcome_count']}",
                ""
            ]

            if enrichment.metrics_discovered:
                output.append("## Discovered Metrics")
                for m in enrichment.metrics_discovered[:10]:
                    output.append(f"- {m}")
                output.append("")

            output.append("## Persona Examples")
            for persona_key, examples in enrichment.persona_examples.items():
                persona_name = CLIENT_PERSONAS[persona_key]["display_name"]
                output.append(f"\n### {persona_name}")
                for ex in examples[:3]:
                    output.append(f"- [{ex.proof_tier}] {ex.domain}: {ex.enriched_text[:100]}...")

            if enrichment.foundever_specific.get("differentiators"):
                output.append("\n## Key Differentiators")
                for diff in enrichment.foundever_specific["differentiators"][:5]:
                    output.append(f"- {diff[:100]}...")

            return "\n".join(output)

        elif name == "convert_to_practitioner_voice":
            enricher = get_lazy_enricher(use_llm=False)

            alternatives = enricher.generate_practitioner_examples(
                marketing_phrase=arguments["marketing_phrase"],
                domain=arguments.get("domain", "Customer Experience Operations"),
                persona=arguments.get("persona", "retail_bank"),
                count=arguments.get("count", 3)
            )

            output = [
                f"# Marketing to Practitioner Voice",
                f"**Original:** \"{arguments['marketing_phrase']}\"",
                f"**Domain:** {arguments.get('domain', 'Customer Experience Operations')}",
                "",
                "## Practitioner Alternatives"
            ]

            for i, alt in enumerate(alternatives, 1):
                output.append(f"\n### {i}. [{alt['proof_tier']}]")
                output.append(f"{alt['practitioner_version']}")
                if alt.get("metrics_used"):
                    output.append(f"**Metrics:** {', '.join(alt['metrics_used'][:2])}")
                if alt.get("source"):
                    output.append(f"**Source:** {alt['source'][:60]}...")

            return "\n".join(output)

        elif name == "get_foundever_evidence":
            searcher = get_lazy_searcher()
            evidence = searcher.get_provider_evidence(
                "Foundever",
                domains=arguments.get("domains")
            )

            output = [
                "# Foundever Evidence Summary",
                f"**Total Claims:** {evidence['total_claims']:,}",
                "",
                "## By Proof Tier"
            ]
            for tier, count in sorted(evidence["by_proof_tier"].items()):
                pct = (count / evidence["total_claims"]) * 100 if evidence["total_claims"] > 0 else 0
                output.append(f"- {tier}: {count:,} ({pct:.1f}%)")

            output.append("\n## By Buyer Domain")
            for domain, claims in sorted(evidence["by_domain"].items(), key=lambda x: -len(x[1]))[:8]:
                output.append(f"- {domain}: {len(claims)} claims")

            output.append("\n## Top Outcomes (T1+/T2)")
            for outcome in evidence["top_outcomes"][:8]:
                output.append(f"- [{outcome['proof_tier']}] {outcome['text'][:80]}...")

            return "\n".join(output)

        elif name == "get_taxonomy":
            output = ["# Buyer Domain Taxonomy", ""]
            for domain, info in BUYER_DOMAIN_TAXONOMY.items():
                output.append(f"## {domain}")
                output.append(f"_{info['description']}_")
                output.append(f"\n**Sub-functions:** {', '.join(info['sub_functions'])}")
                output.append(f"**Metrics:** {', '.join(info['metrics'])}")
                output.append("")
            return "\n".join(output)

        elif name == "get_personas":
            output = ["# Client Personas", ""]
            for key, persona in CLIENT_PERSONAS.items():
                output.append(f"## {persona['display_name']} (`{key}`)")
                output.append(f"_{persona['description']}_")
                output.append(f"\n**Domains:** {', '.join(persona['domains'])}")
                output.append(f"**Keywords:** {', '.join(persona['keywords'][:5])}")
                output.append(f"**Regulatory Focus:** {', '.join(persona['regulatory_focus'])}")
                output.append("")
            return "\n".join(output)

        elif name == "enrich_taxonomy":
            enricher = get_lazy_enricher(use_llm=False)
            enriched = enricher.enrich_taxonomy(provider=arguments.get("provider", "Foundever"))

            output = ["# Taxonomy Enrichment", ""]
            for domain, tax in enriched.items():
                output.append(f"## {domain}")
                output.append(f"Evidence count: {tax.evidence_count}")
                if tax.discovered_metrics:
                    output.append(f"\n**New Metrics:**")
                    for m in tax.discovered_metrics[:5]:
                        output.append(f"- {m}")
                if tax.discovered_capabilities:
                    output.append(f"\n**Capabilities:**")
                    for c in tax.discovered_capabilities[:3]:
                        output.append(f"- {c}")
                output.append("")

            return "\n".join(output)

        # ========== STYLE GUIDE TOOL HANDLERS ==========
        elif name == "get_style_guide":
            section = arguments.get("section", "all")

            output = ["# Foundever RFP & Proposal Style Guide", ""]

            if section in ["all", "structure"]:
                output.extend([
                    "## The '1 Plus' Structure",
                    f"_{ONE_PLUS_STRUCTURE['description']}_",
                    "",
                    "**Pattern:**"
                ])
                for step in ONE_PLUS_STRUCTURE["pattern"]:
                    output.append(f"- {step}")
                output.extend([
                    "",
                    f"**Anti-pattern:** {ONE_PLUS_STRUCTURE['anti_pattern']}",
                    ""
                ])

            if section in ["all", "voice"]:
                output.extend([
                    "## Write Like a Practitioner, Not a Marketer",
                    "",
                    "**Practitioner voice characteristics:**",
                    "- States facts without superlatives",
                    "- Acknowledges tradeoffs and challenges",
                    "- Uses specific numbers, not ranges",
                    "- Describes what happens operationally",
                    "",
                    "| Marketing Voice | Practitioner Voice |",
                    "|-----------------|-------------------|"
                ])
                for conv in VOICE_CONVERSIONS["marketing_to_practitioner"][:5]:
                    output.append(f"| {conv['marketing']} | {conv['practitioner']} |")
                output.append("")

            if section in ["all", "confidence"]:
                output.extend([
                    "## The Confidence Spectrum",
                    "",
                    "| Claim Type | Appropriate Confidence |",
                    "|------------|------------------------|",
                    "| Operational capability | Direct assertion: 'We deliver...' |",
                    "| Track record | Specific evidence: 'Since 2004, across 7 sites...' |",
                    "| Cost savings | Clear math: '$7.59M → $5.02M (34% savings)' |",
                    "| Future projections | Qualified: 'Indicative trajectory,' 'Requires joint discovery' |",
                    "| Technology benefits | Metric-backed: 'Cuts training time by ~40%' |",
                    ""
                ])

            if section in ["all", "formatting"]:
                output.extend([
                    "## Formatting Guidelines",
                    "",
                    "**Typography Hierarchy:**",
                    "- H1: Major sections",
                    "- H2: Subsections",
                    "- H3: Detail categories",
                    "- **Bold**: Key terms, metrics",
                    "- *Italics*: Framing statements, quotes",
                    "- ***Bold italics***: Value statements",
                    "",
                    "**Numbers:**",
                    "- Dollars: $7.59M",
                    "- Percentages: 34%",
                    "- Approximations: ~40%",
                    "- Large counts: 2,500+",
                    ""
                ])

            if section in ["all", "quality_checklist"]:
                output.extend([
                    "## Quality Checklist",
                    "",
                    "**Structure:**",
                    "- [ ] Document leads with operational capability",
                    "- [ ] Value-adds positioned as 'included'",
                    "- [ ] Every major section ends with Value statement",
                    "",
                    "**Language:**",
                    "- [ ] No generic superlatives",
                    "- [ ] Specific numbers instead of ranges",
                    "- [ ] Client name appears throughout",
                    "",
                    "**Tone:**",
                    "- [ ] Sounds like practitioner, not marketer",
                    "- [ ] Confidence matches claim type",
                    "- [ ] No implications client must 'do something'",
                    ""
                ])

            return "\n".join(output)

        elif name == "get_narrative_templates":
            category = arguments["category"]

            output = ["# Narrative Templates", ""]

            categories = [category] if category != "all" else NARRATIVE_TEMPLATES.keys()

            for cat in categories:
                if cat in NARRATIVE_TEMPLATES:
                    output.append(f"## {cat.replace('_', ' ').title()}")
                    for name_key, template in NARRATIVE_TEMPLATES[cat].items():
                        output.append(f"\n**{name_key.replace('_', ' ').title()}:**")
                        output.append(f"> {template}")
                    output.append("")

            return "\n".join(output)

        elif name == "check_voice":
            text = arguments["text"]
            suggest = arguments.get("suggest_alternatives", True)

            issues = []

            # Check for phrases to avoid
            text_lower = text.lower()
            for phrase, reason in PHRASES_TO_AVOID.items():
                if phrase.lower() in text_lower:
                    issues.append({"phrase": phrase, "reason": reason, "type": "avoid"})

            # Check for AI-sounding patterns
            for conv in VOICE_CONVERSIONS["ai_to_human"]:
                if conv["ai"].lower() in text_lower or any(
                    word in text_lower for word in ["holistic", "leverage", "seamlessly", "robust", "cutting-edge"]
                ):
                    if conv["ai"].lower() in text_lower:
                        issues.append({"phrase": conv["ai"], "alternative": conv["human"], "type": "ai_sounding"})

            output = ["# Voice Analysis", "", f"**Input:** {text[:200]}...", ""]

            if issues:
                output.append(f"## Issues Found: {len(issues)}")
                for issue in issues:
                    if issue["type"] == "avoid":
                        output.append(f"\n❌ **\"{issue['phrase']}\"**")
                        output.append(f"   Reason: {issue['reason']}")
                    else:
                        output.append(f"\n⚠️ **AI-sounding:** \"{issue['phrase']}\"")
                        output.append(f"   Alternative: \"{issue['alternative']}\"")
            else:
                output.append("✅ No obvious voice issues detected.")

            if suggest and issues:
                output.extend([
                    "",
                    "## Practitioner Voice Examples",
                    ""
                ])
                for conv in VOICE_CONVERSIONS["marketing_to_practitioner"][:3]:
                    output.append(f"- \"{conv['practitioner']}\"")

            return "\n".join(output)

        elif name == "get_finserv_persona":
            persona_key = arguments["persona"]

            if persona_key not in FINSERV_PERSONAS:
                return f"Unknown persona: {persona_key}"

            persona = FINSERV_PERSONAS[persona_key]

            output = [
                f"# {persona['display_name']}",
                f"*{persona['description']}*",
                "",
                f"**Typical Needs:** {persona['typical_needs']}",
                "",
                "**Service Types:**"
            ]
            for svc in persona["service_types"]:
                output.append(f"- {svc}")

            if persona_key in PERSONA_VALUE_STATEMENTS:
                output.extend([
                    "",
                    "## Recommended Value Statement",
                    f"***Value for {persona['display_name']}:** {PERSONA_VALUE_STATEMENTS[persona_key]}*"
                ])

            return "\n".join(output)

        elif name == "get_threat_context":
            threat_key = arguments["threat"]

            output = ["# Threat/Context Descriptions", ""]

            threats = [threat_key] if threat_key != "all" else THREAT_CONTEXTS.keys()

            for key in threats:
                if key in THREAT_CONTEXTS:
                    t = THREAT_CONTEXTS[key]
                    output.extend([
                        f"## {t['title']}",
                        f"**{t['stat']}** | {t['source']}",
                        "",
                        t['context'],
                        "",
                        f"**Our commitment:** {t['commitment']}",
                        ""
                    ])

            return "\n".join(output)

        elif name == "get_phrases":
            phrase_type = arguments.get("type", "both")

            output = ["# RFP Phrases Guide", ""]

            if phrase_type in ["use", "both"]:
                output.extend(["## Phrases to Use", ""])
                for purpose, phrase in PHRASES_TO_USE.items():
                    output.append(f"| **{purpose.replace('_', ' ').title()}** | {phrase} |")
                output.append("")

            if phrase_type in ["avoid", "both"]:
                output.extend(["## Phrases to Avoid", ""])
                output.append("| Phrase | Why |")
                output.append("|--------|-----|")
                for phrase, reason in PHRASES_TO_AVOID.items():
                    output.append(f"| {phrase} | {reason} |")

            return "\n".join(output)

        elif name == "get_anti_patterns":
            pattern_key = arguments.get("pattern", "all")

            output = ["# Anti-Patterns to Avoid", ""]

            patterns = [pattern_key] if pattern_key != "all" else ANTI_PATTERNS.keys()

            for key in patterns:
                if key in ANTI_PATTERNS:
                    p = ANTI_PATTERNS[key]
                    output.extend([
                        f"## {key.replace('_', ' ').title()}",
                        "",
                        f"❌ **Bad:** {p['bad']}",
                        "",
                        f"✅ **Good:** {p['good']}",
                        "",
                        f"**Why:** {p['why']}",
                        ""
                    ])

            return "\n".join(output)

        elif name == "get_finserv_metrics":
            category = arguments.get("category", "all")

            output = ["# Financial Services Metrics", ""]

            categories = [category] if category != "all" else FINSERV_METRICS.keys()

            for cat in categories:
                if cat in FINSERV_METRICS:
                    output.append(f"## {cat.title()}")
                    for metric in FINSERV_METRICS[cat]:
                        output.append(f"- {metric}")
                    output.append("")

            return "\n".join(output)

        elif name == "build_section":
            topic = arguments["topic"]
            persona_key = arguments["persona"]
            include_evidence = arguments.get("include_evidence", True)

            if persona_key not in FINSERV_PERSONAS:
                return f"Unknown persona: {persona_key}"

            persona = FINSERV_PERSONAS[persona_key]

            # Get evidence from Qdrant if requested
            evidence = []
            metrics = []
            if include_evidence:
                try:
                    searcher = get_lazy_searcher()
                    results = searcher.search_claims(
                        query=topic,
                        limit=10,
                        provider_filter="Foundever"
                    )
                    evidence = results[:5]
                    # Extract any metrics from evidence
                    import re
                    for r in results:
                        nums = re.findall(r'\d+(?:\.\d+)?%|\$[\d,]+(?:\.\d+)?[MBK]?|\d+(?:,\d+)*\+?', r.text)
                        metrics.extend(nums[:2])
                except Exception as e:
                    logger.warning(f"Could not fetch evidence: {e}")

            # Build section
            output = [
                f"# {topic.title()}",
                "",
                f"*Delivering operational excellence for {persona['display_name']}*",
                ""
            ]

            if metrics:
                unique_metrics = list(dict.fromkeys(metrics[:4]))
                output.append("| " + " | ".join(unique_metrics) + " |")
                output.append("|" + "|".join(["---"] * len(unique_metrics)) + "|")
                output.append("")

            output.extend([
                "## The Point",
                "",
                f"For {persona['display_name']} operations, {topic} requires {persona['typical_needs'].lower()}.",
                ""
            ])

            if evidence:
                output.append("## Evidence")
                for e in evidence[:3]:
                    tier = f"[{e.proof_tier}]" if e.proof_tier else "[T1]"
                    output.append(f"- {tier} {e.text[:150]}...")
                output.append("")

            # Value statement
            value = PERSONA_VALUE_STATEMENTS.get(persona_key, f"Operational excellence tailored to {persona['display_name']} requirements.")
            output.append(f"***Value for {persona['display_name']}:** {value}*")

            return "\n".join(output)

        # ========== RESEARCH GUIDANCE TOOL HANDLERS ==========
        elif name == "get_research_guidelines":
            section = arguments.get("section", "all")

            output = [RESEARCH_MODE_HEADER]

            # Always show fabrication warning first
            if section == "all":
                output.extend([
                    "## ⛔ CRITICAL: NO FABRICATION POLICY",
                    "",
                    "**NEVER fabricate information to fill gaps. NEVER.**",
                    "",
                    "If data is missing:",
                    "- Use `{{placeholder}}` format",
                    "- List what information is needed",
                    "- Iterate with user for real facts",
                    "",
                    "**Goal: Build narrative → Placeholder facts → Iterate with user**",
                    "",
                    "A proposal with `{{placeholders}}` is BETTER than one with fabricated statistics.",
                    "",
                    "---",
                    ""
                ])

            if section in ["all", "priority"]:
                output.extend([
                    "## Priority Hierarchy",
                    ""
                ])
                for item in RESEARCH_GUIDELINES["priority_hierarchy"]["order"]:
                    output.append(f"**{item['priority']}. {item['source']}**: {item['description']}")
                output.append("")

            if section in ["all", "validation"]:
                output.extend([
                    "## Validation Rules",
                    ""
                ])
                for rule in RESEARCH_GUIDELINES["validation_rules"]:
                    output.append(f"- {rule}")
                output.append("")

            if section in ["all", "solution_approach"]:
                output.extend([
                    "## Solution Approach",
                    f"*{RESEARCH_GUIDELINES['solution_approach']['principle']}*",
                    ""
                ])
                for rule in RESEARCH_GUIDELINES["solution_approach"]["rules"]:
                    output.append(f"- {rule}")
                output.append("")

            if section in ["all", "qdrant_vs_external"]:
                qve = RESEARCH_GUIDELINES["qdrant_vs_external"]
                output.extend([
                    "## When to Use Qdrant vs External Research",
                    "",
                    "### Use Qdrant For:"
                ])
                for item in qve["use_qdrant_for"]:
                    output.append(f"- {item}")
                output.extend(["", "### Use External Research For:"])
                for item in qve["use_external_for"]:
                    output.append(f"- {item}")
                output.extend(["", "### AVOID External Research For (redundant):"])
                for item in qve["avoid_external_for"]:
                    output.append(f"- ❌ {item}")
                output.append("")

            if section in ["all", "attribution"]:
                output.extend([
                    "## Claim Attribution Format",
                    "",
                    "**EVERY statistic MUST have a source. No orphan numbers.**",
                    ""
                ])
                for source, fmt in RESEARCH_GUIDELINES["claim_attribution_format"].items():
                    output.append(f"- **{source}**: `{fmt}`")
                output.append("")

            # Always include pricing restrictions
            if section == "all":
                pricing = RESEARCH_GUIDELINES.get("pricing_restrictions", {})
                output.extend([
                    "## ⚠️ PRICING RESTRICTIONS",
                    "",
                    f"**Rule:** {pricing.get('rule', 'NEVER discuss specific pricing')}",
                    "",
                    "**Forbidden Topics:**"
                ])
                for item in pricing.get("forbidden", []):
                    output.append(f"- ❌ {item}")
                output.extend([
                    "",
                    f"**Exception:** {pricing.get('exception', 'Outcome-based pricing as solution concept')}",
                    "",
                    f"**If user asks about pricing:** {pricing.get('if_user_asks_about_pricing', 'Redirect to commercial model options')}",
                    ""
                ])

            return "\n".join(output)

        elif name == "validate_claim":
            claim = arguments["claim"]
            provider = arguments.get("provider", "Foundever")

            try:
                searcher = get_lazy_searcher()
                results = searcher.search_claims(
                    query=claim,
                    limit=10,
                    provider_filter=provider
                )

                # Analyze results for confidence level
                t3_count = sum(1 for r in results if r.proof_tier == "T3_third_party_recognition" and r.score > 0.7)
                t2_count = sum(1 for r in results if r.proof_tier == "T2_case_study" and r.score > 0.7)
                t1_count = sum(1 for r in results if r.proof_tier == "T1_vendor_artifact" and r.score > 0.7)
                t0_count = sum(1 for r in results if r.proof_tier == "T0_marketing" and r.score > 0.7)

                high_match = any(r.score > 0.85 for r in results)

                if t2_count > 0 or t3_count > 0:
                    confidence = CLAIM_CONFIDENCE["validated"]
                elif t1_count > 0 or (t0_count >= 3 and high_match):
                    confidence = CLAIM_CONFIDENCE["supported"]
                elif t0_count > 0:
                    confidence = CLAIM_CONFIDENCE["inferred"]
                elif results and results[0].score > 0.6:
                    confidence = CLAIM_CONFIDENCE["unvalidated"]
                else:
                    confidence = CLAIM_CONFIDENCE["missing"]

                output = [
                    "# Claim Validation",
                    "",
                    f"**Claim:** {claim}",
                    f"**Provider:** {provider}",
                    "",
                    f"## Confidence: {confidence['label']}",
                    f"_{confidence['description']}_",
                    ""
                ]

                if confidence.get("qualifier"):
                    output.append(f"**Use this qualifier:** {confidence['qualifier']}")
                    output.append("")

                output.extend([
                    "## Evidence Found",
                    f"- T3 (Third-party): {t3_count}",
                    f"- T2 (Case study): {t2_count}",
                    f"- T1 (Vendor artifact): {t1_count}",
                    f"- T0 (Marketing): {t0_count}",
                    ""
                ])

                if results[:3]:
                    output.append("## Top Matches")
                    for r in results[:3]:
                        output.append(f"- [{r.proof_tier}] (score: {r.score:.2f}) {r.text[:100]}...")

                output.extend([
                    "",
                    "## Attribution",
                    f"If using this claim, cite as: `[Qdrant:{results[0].proof_tier if results else 'UNVALIDATED'}] {claim[:50]}...`"
                ])

                return "\n".join(output)

            except Exception as e:
                return f"Error validating claim: {str(e)}"

        elif name == "get_solution_options":
            need = arguments["need"]
            persona_key = arguments["persona"]
            constraints = arguments.get("constraints", [])

            if persona_key not in FINSERV_PERSONAS:
                return f"Unknown persona: {persona_key}"

            persona = FINSERV_PERSONAS[persona_key]

            # Search for relevant evidence
            try:
                searcher = get_lazy_searcher()
                results = searcher.search_claims(
                    query=need,
                    limit=15,
                    provider_filter="Foundever"
                )
            except:
                results = []

            output = [
                RESEARCH_MODE_HEADER,
                f"# Solution Options for: {need}",
                f"**Persona:** {persona['display_name']}",
                ""
            ]

            if constraints:
                output.append("**Known Constraints:**")
                for c in constraints:
                    output.append(f"- {c}")
                output.append("")

            output.extend([
                "---",
                "",
                "## Option 1: Conservative Approach",
                "*Lower risk, proven methods*",
                "",
                "**Approach:** Leverage existing proven capabilities with minimal customization",
                "",
                "**Pros:**",
                "- Faster implementation",
                "- Lower risk",
                "- Proven track record",
                "",
                "**Challenges:**",
                "- May not fully address unique requirements",
                "- Less differentiation",
                "",
                "**Dependencies:** [NEEDS USER INPUT]",
                "",
                "---",
                "",
                "## Option 2: Balanced Approach",
                "*Moderate customization with proven foundation*",
                "",
                "**Approach:** Start with proven model, add targeted customization",
                "",
                "**Pros:**",
                "- Balances speed and customization",
                "- Builds on evidence base",
                "",
                "**Challenges:**",
                "- Requires more discovery",
                "- Timeline may extend",
                "",
                "**Dependencies:** [NEEDS USER INPUT]",
                "",
                "---",
                "",
                "## Option 3: Transformative Approach",
                "*Higher investment, differentiated outcome*",
                "",
                "**Approach:** Custom solution designed for specific requirements",
                "",
                "**Pros:**",
                "- Fully addresses unique needs",
                "- Maximum differentiation",
                "",
                "**Challenges:**",
                "- Longer timeline",
                "- Higher risk",
                "- Requires significant discovery",
                "",
                "**Dependencies:** [NEEDS USER INPUT]",
                "",
                "---",
                "",
                "## Questions to Clarify Before Proceeding",
                "",
                "1. What is the primary success metric?",
                "2. What is the timeline constraint?",
                "3. What is the budget envelope?",
                "4. Are there regulatory/compliance constraints?",
                "5. What is the risk tolerance?",
                "",
                "**[UNVALIDATED]** These options are templates. User input required to refine."
            ])

            if results[:3]:
                output.extend([
                    "",
                    "---",
                    "",
                    "## Relevant Evidence from Qdrant"
                ])
                for r in results[:3]:
                    output.append(f"- [{r.proof_tier}] {r.text[:100]}...")

            return "\n".join(output)

        elif name == "check_qdrant_coverage":
            topic = arguments["topic"]
            provider = arguments.get("provider", "Foundever")

            try:
                searcher = get_lazy_searcher()
                results = searcher.search_claims(
                    query=topic,
                    limit=50,
                    provider_filter=provider
                )

                # Count by tier
                tier_counts = {}
                for r in results:
                    tier = r.proof_tier or "T0_marketing"
                    tier_counts[tier] = tier_counts.get(tier, 0) + 1

                high_quality = sum(1 for r in results if r.proof_tier in ["T2_case_study", "T3_third_party_recognition"])
                total = len(results)

                # Determine recommendation
                if high_quality >= 5:
                    recommendation = "USE QDRANT ONLY - Strong T2/T3 evidence available"
                    rec_icon = "✅"
                elif total >= 10:
                    recommendation = "QDRANT PRIMARY - Supplement with external for gaps"
                    rec_icon = "🔶"
                elif total >= 3:
                    recommendation = "QDRANT + EXTERNAL - Limited coverage, external research recommended"
                    rec_icon = "⚠️"
                else:
                    recommendation = "EXTERNAL NEEDED - Minimal Qdrant coverage"
                    rec_icon = "❌"

                output = [
                    "# Qdrant Coverage Check",
                    "",
                    f"**Topic:** {topic}",
                    f"**Provider:** {provider}",
                    "",
                    f"## {rec_icon} Recommendation: {recommendation}",
                    "",
                    "## Evidence by Proof Tier",
                    f"- T3 (Third-party validation): {tier_counts.get('T3_third_party_recognition', 0)}",
                    f"- T2 (Case studies): {tier_counts.get('T2_case_study', 0)}",
                    f"- T1 (Vendor artifacts): {tier_counts.get('T1_vendor_artifact', 0)}",
                    f"- T0 (Marketing): {tier_counts.get('T0_marketing', 0)}",
                    f"- **Total:** {total}",
                    ""
                ]

                if results[:5]:
                    output.append("## Sample Claims")
                    for r in results[:5]:
                        output.append(f"- [{r.proof_tier}] {r.text[:120]}...")
                    output.append("")

                # Identify gaps
                output.extend([
                    "## Potential Gaps (may need external research)",
                    ""
                ])
                if tier_counts.get("T3_third_party_recognition", 0) == 0:
                    output.append("- ⚠️ No third-party validation found")
                if tier_counts.get("T2_case_study", 0) == 0:
                    output.append("- ⚠️ No case study evidence found")
                if total < 5:
                    output.append("- ⚠️ Low overall coverage")

                output.extend([
                    "",
                    "## What NOT to search externally",
                    "- Foundever.com (already in Qdrant)",
                    "- Generic BPO capabilities (already captured)",
                    "- Marketing claims (low value, already have T0)"
                ])

                return "\n".join(output)

            except Exception as e:
                return f"Error checking coverage: {str(e)}"

        elif name == "format_sourced_content":
            content = arguments["content"]
            evidence = arguments.get("evidence", [])

            output = [
                "# Sourced Content",
                "",
                "## Original Content",
                content,
                "",
                "## Attribution Notes",
                "",
                "Every claim in final content should use one of these formats:",
                "",
                "- `[Qdrant:T2_case_study]` - For validated case study evidence",
                "- `[Qdrant:T1_vendor_artifact]` - For vendor documentation",
                "- `[User]` - For user-provided information",
                "- `[Style Guide]` - For style guide principles",
                "- `[External:source_name]` - For external research",
                "- `[Inference from X, Y]` - For logical conclusions",
                "- `[UNVALIDATED]` - For assumptions needing confirmation",
                ""
            ]

            if evidence:
                output.extend([
                    "## Evidence Sources Provided",
                    ""
                ])
                for e in evidence:
                    output.append(f"- {e}")

            output.extend([
                "",
                "## Reminder",
                "- No claims without attribution",
                "- Flag missing information explicitly",
                "- Distinguish FACT from INFERENCE",
                "- EVERY statistic must have a source"
            ])

            return "\n".join(output)

        elif name == "check_content_compliance":
            content = arguments["content"]

            pricing_issues = []
            stat_issues = []

            # Check for pricing violations
            pricing_patterns = [
                (r'\$[\d,]+(?:\.\d+)?(?:\s*(?:per|/)\s*(?:hour|hr|FTE|agent|seat|month|year))?', 'Dollar amount with rate'),
                (r'(?:hourly|annual|monthly)\s+(?:rate|cost|price|fee)', 'Rate terminology'),
                (r'(?:cost|price|rate)\s+(?:of|per|at)\s+\$', 'Cost with dollar sign'),
                (r'\$[\d,]+[MBK]?\s+(?:contract|deal|engagement)', 'Contract value'),
                (r'(?:rate\s+card|pricing\s+tier|price\s+list)', 'Pricing documentation'),
                (r'(?:budget|spend|investment)\s+(?:of|at|around)\s+\$[\d,]+', 'Budget figures'),
                (r'\$[\d.]+\s*/\s*(?:hr|hour|FTE|head)', 'Per-unit pricing'),
            ]

            for pattern, desc in pricing_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                for match in matches:
                    pricing_issues.append({"match": match, "type": desc})

            # Check for unsourced statistics
            # Find all statistics (numbers with %, $, or context suggesting metrics)
            stat_patterns = [
                r'\d+(?:\.\d+)?%',  # Percentages
                r'\$[\d,]+(?:\.\d+)?[MBK]?',  # Dollar amounts
                r'\d+(?:,\d+)*\+?\s*(?:agents?|FTEs?|employees?|clients?|sites?|locations?)',  # Counts
                r'(?:reduced|increased|improved|decreased)\s+(?:by\s+)?\d+',  # Changes
                r'\d+(?:\.\d+)?\s*(?:days?|hours?|minutes?|weeks?|months?)',  # Time metrics
                r'(?:top|bottom)\s*\d+',  # Rankings
            ]

            # Check if statistics have source attribution nearby
            for pattern in stat_patterns:
                for match in re.finditer(pattern, content, re.IGNORECASE):
                    stat = match.group()
                    # Check if there's a source attribution within 100 chars
                    start = max(0, match.start() - 50)
                    end = min(len(content), match.end() + 100)
                    context = content[start:end]

                    has_source = bool(re.search(r'\[(?:Qdrant|User|Style Guide|External|Source)[^\]]*\]', context, re.IGNORECASE))

                    if not has_source:
                        stat_issues.append({"stat": stat, "context": context[:80]})

            # Build output
            output = [
                "# Content Compliance Check",
                "",
                f"**Content Length:** {len(content)} characters",
                ""
            ]

            if pricing_issues:
                output.extend([
                    "## ❌ PRICING VIOLATIONS FOUND",
                    "",
                    "**These MUST be removed:**",
                    ""
                ])
                for issue in pricing_issues:
                    output.append(f"- `{issue['match']}` ({issue['type']})")
                output.extend([
                    "",
                    "**Rule:** Never discuss specific pricing, rates, or costs.",
                    "**Exception:** Outcome-based pricing as a solution concept only.",
                    ""
                ])
            else:
                output.append("## ✅ No pricing violations found")
                output.append("")

            if stat_issues:
                output.extend([
                    "## ⚠️ UNSOURCED STATISTICS FOUND",
                    "",
                    "**These MUST have source attribution:**",
                    ""
                ])
                for issue in stat_issues[:10]:  # Limit to first 10
                    output.append(f"- `{issue['stat']}` in: ...{issue['context']}...")
                if len(stat_issues) > 10:
                    output.append(f"- ...and {len(stat_issues) - 10} more")
                output.extend([
                    "",
                    "**Required format:** `[Qdrant:T2_case_study]` or `[External:source_name]`",
                    ""
                ])
            else:
                output.append("## ✅ All statistics appear to have sources")
                output.append("")

            # Summary
            if pricing_issues or stat_issues:
                output.extend([
                    "---",
                    "## Action Required",
                    "",
                    f"- Pricing issues to fix: {len(pricing_issues)}",
                    f"- Statistics needing sources: {len(stat_issues)}",
                    "",
                    "**Content is NOT compliant. Fix issues before using.**"
                ])
            else:
                output.extend([
                    "---",
                    "## ✅ Content is COMPLIANT",
                    "",
                    "No pricing violations or unsourced statistics detected."
                ])

            return "\n".join(output)

        elif name == "get_outcome_based_pricing_framing":
            pricing_config = RESEARCH_GUIDELINES.get("pricing_restrictions", {})

            output = [
                "# Outcome-Based Pricing: Approved Framing",
                "",
                "## When to Use",
                "This is the ONLY pricing topic you may discuss proactively.",
                "Use when iterating with users on commercial model options.",
                "",
                "## Approved Talking Points",
                ""
            ]

            for point in pricing_config.get("outcome_based_framing", []):
                output.append(f"- {point}")

            output.extend([
                "",
                "## How to Position",
                "",
                "1. **Frame as alignment:** 'Outcome-based models align our incentives with your success'",
                "2. **Emphasize shared risk:** 'We share the risk and reward based on delivered results'",
                "3. **Focus on metrics:** 'Payment tied to metrics you already track'",
                "4. **Iterate on structure:** 'Several models exist—let's find what fits your priorities'",
                "",
                "## Questions to Iterate with User",
                "",
                "1. What are your primary success metrics for this program?",
                "2. Which outcomes matter most: cost reduction, quality improvement, or speed?",
                "3. How do you currently measure vendor performance?",
                "4. What's your appetite for shared-risk commercial models?",
                "5. Are there specific KPIs that would make sense as payment triggers?",
                "",
                "## What NOT to Discuss",
                "",
                "❌ Specific dollar amounts",
                "❌ Hourly rates",
                "❌ Per-FTE costs",
                "❌ Contract values",
                "❌ Rate comparisons",
                "",
                "## If User Asks for Specific Pricing",
                "",
                "Redirect: 'Specific pricing requires a scoping conversation with our commercial team. ",
                "I can help you think through which commercial MODEL might fit best—fixed, outcome-based, ",
                "or hybrid—and what success metrics would apply.'"
            ])

            return "\n".join(output)

        elif name == "get_no_fabrication_policy":
            policy = RESEARCH_GUIDELINES.get("no_fabrication_policy", {})

            output = [
                "# ⚠️ NO FABRICATION POLICY",
                "",
                f"**Rule:** {policy.get('rule', 'NEVER fabricate information')}",
                "",
                "## What Counts as Fabrication (NEVER DO THIS)",
                ""
            ]
            for item in policy.get("what_counts_as_fabrication", []):
                output.append(f"- ❌ {item}")

            output.extend([
                "",
                "## Correct Approach",
                ""
            ])
            for item in policy.get("correct_approach", []):
                output.append(f"- ✅ {item}")

            output.extend([
                "",
                "## Placeholder Format",
                "",
                "When data is missing, use these formats:",
                ""
            ])
            for ptype, fmt in policy.get("placeholder_format", {}).items():
                output.append(f"- **{ptype}**: `{fmt}`")

            output.extend([
                "",
                "## Iteration Template",
                "",
                "When you need information from user:",
                "",
                "```",
                policy.get("iteration_prompt", "I need verified information to complete this section."),
                "```",
                "",
                "## The Goal",
                "",
                "**Build narrative structure → Placeholder facts → Iterate with user**",
                "",
                "NOT: Fill in plausible-sounding data to make it 'complete'",
                "",
                "A proposal with {{placeholders}} is BETTER than one with fabricated statistics."
            ])

            return "\n".join(output)

        elif name == "generate_iteration_request":
            section = arguments["section"]
            missing_items = arguments["missing_items"]
            context = arguments.get("context", "")

            output = [
                "# Information Needed from User",
                "",
                f"**Section:** {section}",
                ""
            ]

            if context:
                output.extend([
                    f"**Context:** {context}",
                    ""
                ])

            output.extend([
                "## Missing Information",
                "",
                "To complete this section with verified facts, I need:",
                ""
            ])

            for i, item in enumerate(missing_items, 1):
                output.append(f"{i}. **{item}**")
                output.append(f"   - Placeholder: `{{{{item}}}}`")
                output.append("")

            output.extend([
                "---",
                "",
                "## Options",
                "",
                "1. **Provide the data** - Share verified figures for each item above",
                "2. **Keep placeholders** - I'll continue with `{{placeholders}}` for your team to fill",
                "3. **Scope differently** - Tell me what data IS available and we'll adjust the narrative",
                "",
                "## What I Will NOT Do",
                "",
                "❌ Make up numbers that sound plausible",
                "❌ Extrapolate specific figures from general statements",
                "❌ Fill in details to make the proposal 'complete'",
                "",
                "**Your call - how would you like to proceed?**"
            ])

            return "\n".join(output)

        elif name == "check_for_fabrication":
            content = arguments["content"]
            search_summary = arguments.get("search_results_summary", "")

            suspected = []

            # Patterns that suggest fabrication
            fabrication_patterns = [
                # Precise specific numbers without sources
                (r'(?<!\[)\b(\d{1,3}(?:,\d{3})+)\s+(?:agents?|FTEs?|employees?|seats?|centers?|sites?|locations?)\b(?![^\[]*\])', 'Specific count without source'),
                # Percentages without attribution
                (r'(?<!\[)\b(\d+(?:\.\d+)?%)\s+(?:reduction|increase|improvement|growth|savings)\b(?![^\[]*\])', 'Percentage claim without source'),
                # Dollar amounts in context
                (r'(?<!\[)\$(\d+(?:\.\d+)?[MBK]?)\s+(?:in|of|saved|reduced|increased)\b(?![^\[]*\])', 'Dollar amount without source'),
                # Specific locations/facilities
                (r'\b(?:Dallas|Phoenix|Manila|Montreal|Bogota|Toronto)\s+(?:\d+[\-\s]seat|\d+\s+FTE)', 'Specific facility details'),
                # Year-specific claims
                (r'\bin\s+20\d{2}\b[^\.]*\b(\d+(?:,\d+)*|\d+(?:\.\d+)?%)', 'Year-specific statistic'),
                # Round numbers that look estimated
                (r'\b((?:approximately|about|around|roughly|nearly)\s+)?\b([1-9]0{2,})\b', 'Round number (likely estimated)'),
            ]

            for pattern, desc in fabrication_patterns:
                matches = re.finditer(pattern, content, re.IGNORECASE)
                for match in matches:
                    # Check if it has a source nearby
                    start = max(0, match.start() - 30)
                    end = min(len(content), match.end() + 50)
                    context = content[start:end]

                    has_source = bool(re.search(r'\[(?:Qdrant|User|External|Source)[^\]]*\]', context))

                    if not has_source:
                        suspected.append({
                            "text": match.group(),
                            "type": desc,
                            "context": context.strip()
                        })

            output = [
                "# Fabrication Check Results",
                "",
                f"**Content scanned:** {len(content)} characters",
                ""
            ]

            if search_summary:
                output.extend([
                    "## What Was Actually Found in Searches",
                    "",
                    search_summary,
                    ""
                ])

            if suspected:
                output.extend([
                    f"## ⚠️ {len(suspected)} Suspected Fabrications Found",
                    "",
                    "These items appear to be invented (no source attribution):",
                    ""
                ])

                for i, item in enumerate(suspected[:15], 1):
                    output.append(f"### {i}. `{item['text']}`")
                    output.append(f"**Type:** {item['type']}")
                    output.append(f"**Context:** ...{item['context']}...")
                    output.append(f"**Fix:** Replace with `{{{{placeholder}}}}` or add `[Source]`")
                    output.append("")

                if len(suspected) > 15:
                    output.append(f"*...and {len(suspected) - 15} more*")
                    output.append("")

                output.extend([
                    "---",
                    "",
                    "## Required Action",
                    "",
                    "For each suspected fabrication:",
                    "1. **If you have a source:** Add `[Qdrant:tier]` or `[External:source]`",
                    "2. **If no source exists:** Replace with `{{placeholder}}`",
                    "3. **If user provided:** Add `[User]` attribution",
                    "",
                    "**Do NOT leave unattributed statistics in the content.**"
                ])
            else:
                output.extend([
                    "## ✅ No Obvious Fabrications Detected",
                    "",
                    "All statistics appear to have source attribution.",
                    "",
                    "*Note: This check is heuristic. Review content manually for accuracy.*"
                ])

            return "\n".join(output)

        # ========== RFP INPUT HANDLING ==========
        elif name == "parse_rfp_requirements":
            doc_text = arguments["document_text"]
            doc_type = arguments.get("document_type", "other")
            persona = arguments.get("client_persona", "unknown")

            output = [
                "# RFP Requirements Analysis",
                "",
                f"**Document Type:** {doc_type}",
                f"**Persona:** {persona}",
                f"**Text Length:** {len(doc_text)} characters",
                "",
                "---",
                "",
                "## Identified Requirements",
                "",
                "*Review and categorize the following:*",
                ""
            ]

            # Extract potential requirements (lines with question marks, numbered items, bullets)
            lines = doc_text.split('\n')
            requirements = []
            questions = []

            for line in lines:
                line = line.strip()
                if not line:
                    continue
                if '?' in line:
                    questions.append(line)
                elif any(line.startswith(p) for p in ['1.', '2.', '3.', '•', '-', '*', 'a)', 'b)']):
                    requirements.append(line)
                elif len(line) > 20 and any(kw in line.lower() for kw in ['require', 'must', 'shall', 'need', 'expect', 'provide', 'describe']):
                    requirements.append(line)

            if requirements:
                output.append("### Extracted Requirements")
                for i, req in enumerate(requirements[:20], 1):
                    output.append(f"{i}. {req[:200]}")
                output.append("")

            if questions:
                output.append("### Questions to Answer")
                for i, q in enumerate(questions[:15], 1):
                    output.append(f"{i}. {q[:200]}")
                output.append("")

            # Identify gaps
            output.extend([
                "## ⚠️ Information Gaps Detected",
                "",
                "Check if the following are specified:",
                ""
            ])

            gap_checks = [
                ("Timeline/Go-live date", any(kw in doc_text.lower() for kw in ['timeline', 'go-live', 'launch', 'start date'])),
                ("Volume/FTE requirements", any(kw in doc_text.lower() for kw in ['volume', 'fte', 'headcount', 'calls', 'contacts'])),
                ("Geographic scope", any(kw in doc_text.lower() for kw in ['location', 'site', 'geography', 'region', 'country'])),
                ("Regulatory requirements", any(kw in doc_text.lower() for kw in ['compliance', 'regulatory', 'pci', 'sox', 'hipaa'])),
                ("Technology/Integration", any(kw in doc_text.lower() for kw in ['integration', 'api', 'crm', 'telephony', 'platform'])),
                ("Success metrics/KPIs", any(kw in doc_text.lower() for kw in ['kpi', 'metric', 'sla', 'performance', 'target'])),
                ("Budget constraints", any(kw in doc_text.lower() for kw in ['budget', 'cost', 'price', 'investment'])),
            ]

            for check, found in gap_checks:
                status = "✅ Mentioned" if found else "❓ NOT FOUND - clarify"
                output.append(f"- {check}: {status}")

            output.extend([
                "",
                "## Next Steps",
                "",
                "1. Use `generate_clarifying_questions` for gaps marked ❓",
                "2. Use `map_to_style_guide_structure` to create response outline",
                "3. Use `track_assumptions` for any assumptions needed"
            ])

            return "\n".join(output)

        elif name == "generate_clarifying_questions":
            requirements = arguments["requirements"]
            identified_gaps = arguments.get("identified_gaps", [])

            output = [
                "# Clarifying Questions for Client",
                "",
                "**Purpose:** Resolve ambiguities before drafting response",
                "",
                "---",
                ""
            ]

            # Standard question categories
            question_categories = {
                "Scope & Volume": [
                    "What is the expected contact volume (calls/chats/emails per month)?",
                    "What is the target FTE count or range?",
                    "Are there seasonal variations in volume? If so, what are peak periods?",
                    "What channels are in scope (voice, chat, email, social)?",
                ],
                "Timeline & Implementation": [
                    "What is the target go-live date?",
                    "Is there flexibility in the timeline?",
                    "Are there any hard deadlines (contract expirations, regulatory)?",
                    "Is this a new program or transition from incumbent?",
                ],
                "Geography & Languages": [
                    "What geographic coverage is required (US only, North America, global)?",
                    "What languages must be supported?",
                    "Are there preferences for delivery locations (onshore, nearshore, offshore)?",
                    "Are there data residency requirements?",
                ],
                "Technology & Integration": [
                    "What CRM/telephony platforms are currently in use?",
                    "What integrations are required vs. nice-to-have?",
                    "Will agents use client systems or can we propose our stack?",
                    "Are there security/authentication requirements (SSO, MFA)?",
                ],
                "Regulatory & Compliance": [
                    "What regulatory frameworks apply (TCPA, FDCPA, Reg E, PCI, etc.)?",
                    "Are there specific compliance certifications required?",
                    "What are the call recording/retention requirements?",
                    "Are there restrictions on offshore handling of certain data?",
                ],
                "Success Metrics": [
                    "What are the primary KPIs for this program?",
                    "What are the target SLA levels?",
                    "How is success measured today (if transitioning)?",
                    "Are there performance guarantees expected?",
                ],
                "Commercial Model": [
                    "What commercial model is preferred (per FTE, per hour, per transaction)?",
                    "Is there interest in outcome-based or performance-based pricing?",
                    "What is the expected contract term?",
                ],
            }

            # Check which questions are relevant based on requirements text
            req_lower = requirements.lower()

            for category, questions in question_categories.items():
                relevant_qs = []
                for q in questions:
                    # Check if question topic is NOT already addressed
                    keywords = q.lower().split()[:3]
                    if not any(kw in req_lower for kw in keywords if len(kw) > 4):
                        relevant_qs.append(q)

                if relevant_qs:
                    output.append(f"## {category}")
                    for q in relevant_qs[:3]:  # Top 3 per category
                        output.append(f"- {q}")
                    output.append("")

            # Add any user-identified gaps
            if identified_gaps:
                output.extend([
                    "## Additional Gaps Identified",
                    ""
                ])
                for gap in identified_gaps:
                    output.append(f"- Clarify: {gap}")
                output.append("")

            output.extend([
                "---",
                "",
                "## How to Use",
                "",
                "1. **Present to user** - Ask them to answer or confirm they don't know",
                "2. **For unanswered questions** - Use `{{placeholder}}` in response",
                "3. **Track assumptions** - Use `track_assumptions` for any guesses",
                "",
                "**Remember:** Don't fabricate answers. Placeholder or ask."
            ])

            return "\n".join(output)

        elif name == "map_to_style_guide_structure":
            requirements = arguments["requirements"]
            persona_key = arguments["persona"]

            persona = FINSERV_PERSONAS.get(persona_key, {})
            persona_name = persona.get("display_name", "{{Client}}")

            output = [
                "# Proposal Structure Map",
                "",
                f"**Client Persona:** {persona_name}",
                "",
                "---",
                "",
                "## Standard Proposal Sections",
                "",
                "*Each section follows the style guide format:*",
                "- Framing statement (italics)",
                "- Key metrics (table)",
                "- 'The Point' explanation",
                "- Supporting evidence",
                "- Value statement for client",
                "",
                "---",
                ""
            ]

            sections = [
                ("1. Executive Summary", "1_plus_structure", [
                    "Lead with operational capability (what they asked for)",
                    "Position value-adds as 'included, not required'",
                    "No action required from client framing"
                ]),
                ("2. Understanding Client Needs", "client_understanding", [
                    "Demonstrate understanding of their specific challenges",
                    "Reference their industry/persona context",
                    "Show you've read and understood the RFP"
                ]),
                ("3. Solution Overview", "solution_design", [
                    "High-level solution architecture",
                    "How it addresses stated requirements",
                    "Differentiation without explicit competitor mentions"
                ]),
                ("4. Delivery Model", "operational", [
                    "Site strategy and rationale",
                    "FTE model and staffing approach",
                    "Hours of operation and coverage"
                ]),
                ("5. Technology & Innovation", "technology", [
                    "Platform capabilities",
                    "Integration approach",
                    "AI/automation where applicable"
                ]),
                ("6. Governance & Compliance", "compliance", [
                    "Regulatory framework coverage",
                    "Certifications and audits",
                    "Risk management approach"
                ]),
                ("7. Implementation & Transition", "transition", [
                    "Timeline with milestones",
                    "Risk mitigation for transition",
                    "Training and ramp approach"
                ]),
                ("8. Team & Leadership", "team", [
                    "Proposed leadership structure",
                    "Account management model",
                    "Escalation paths"
                ]),
                ("9. Proof Points & Evidence", "evidence", [
                    "Relevant case studies (use personas, not names)",
                    "Metrics from similar programs",
                    "Third-party validation"
                ]),
            ]

            for section_name, section_type, guidelines in sections:
                output.append(f"### {section_name}")
                output.append("")
                output.append("**Style Guide Requirements:**")
                for g in guidelines:
                    output.append(f"- {g}")
                output.append("")
                output.append(f"**Requirements to Address:** `{{{{Map relevant requirements here}}}}`")
                output.append("")
                output.append(f"**Evidence Needed:** Use `search_claims` for '{section_type}' + persona keywords")
                output.append("")
                output.append("---")
                output.append("")

            output.extend([
                "## Workflow",
                "",
                "For each section:",
                "1. `get_response_template` - Get the section structure",
                "2. `search_claims` - Find Qdrant evidence",
                "3. `check_qdrant_coverage` - Verify evidence quality",
                "4. Draft with `{{placeholders}}` for missing data",
                "5. `generate_iteration_request` - Ask user for missing facts",
                "6. `check_for_fabrication` - Verify no invented data",
                "7. `llm_fact_check` - Final quality gate"
            ])

            return "\n".join(output)

        elif name == "track_assumptions":
            assumptions = arguments["assumptions"]
            context = arguments.get("context", "")

            output = [
                "# Assumption Tracker",
                "",
                f"**Context:** {context}" if context else "",
                "",
                "⚠️ **These assumptions require user confirmation before proceeding.**",
                "",
                "---",
                ""
            ]

            for i, a in enumerate(assumptions, 1):
                assumption = a.get("assumption", "")
                impact = a.get("impact", "Unknown impact")
                default = a.get("default_if_not_confirmed", "Will use placeholder")

                output.extend([
                    f"## Assumption {i}",
                    "",
                    f"**Assumption:** {assumption}",
                    "",
                    f"**Impact if wrong:** {impact}",
                    "",
                    f"**Default if not confirmed:** {default}",
                    "",
                    "**Status:** ⏳ PENDING CONFIRMATION",
                    "",
                    "---",
                    ""
                ])

            output.extend([
                "## User Response Needed",
                "",
                "For each assumption above, please:",
                "1. **CONFIRM** - Assumption is correct, proceed",
                "2. **CORRECT** - Provide the accurate information",
                "3. **UNKNOWN** - We'll use `{{placeholder}}` instead",
                "",
                "**Do NOT proceed with unconfirmed assumptions in final content.**"
            ])

            return "\n".join(output)

        elif name == "get_response_template":
            section_type = arguments["section_type"]
            persona_key = arguments.get("persona")

            persona = FINSERV_PERSONAS.get(persona_key, {}) if persona_key else {}
            persona_name = persona.get("display_name", "{{Client}}")

            templates = {
                "executive_summary": f"""# Executive Summary

*{{{{Framing statement - one line setting context}}}}*

| {{{{Metric 1}}}} | {{{{Metric 2}}}} | {{{{Metric 3}}}} | {{{{Metric 4}}}} |
|-----------------|-----------------|-----------------|-----------------|
| {{{{Value}}}}    | {{{{Value}}}}    | {{{{Value}}}}    | {{{{Value}}}}    |

## The Point

{{{{2-3 sentences explaining WHY this matters to {persona_name}}}}}

## What You Asked For

{{{{Demonstrate you can execute the operational baseline}}}}

## What You Get With Us

{{{{Position differentiators as included benefits, not requirements}}}}

***Value for {persona_name}:** {{{{Concrete benefit statement}}}}*""",

                "solution_overview": f"""# Solution Overview

*{{{{Framing statement}}}}*

## The Point

{{{{How this solution addresses {persona_name}'s specific needs}}}}

## Solution Architecture

{{{{High-level design - use evidence from Qdrant}}}}

## Key Differentiators

- **{{{{Differentiator 1}}}}:** [Qdrant:proof_tier] {{{{Evidence}}}}
- **{{{{Differentiator 2}}}}:** [Qdrant:proof_tier] {{{{Evidence}}}}

***Value for {persona_name}:** {{{{Outcome statement}}}}*""",

                "delivery_model": f"""# Delivery Model

*Built for {persona_name} requirements*

| Sites | FTE | Languages | Coverage |
|-------|-----|-----------|----------|
| {{{{X}}}} | {{{{X}}}} | {{{{X}}}} | {{{{X}}}} |

## The Point

{{{{Why this delivery model fits {persona_name}}}}}

## Site Strategy

| Location | Capacity | Rationale |
|----------|----------|-----------|
| {{{{Site 1}}}} | {{{{X seats}}}} | {{{{Why this location}}}} |

## Staffing Model

{{{{FTE breakdown, ratios, ramp plan}}}}

**Challenges:** {{{{Honest acknowledgment of tradeoffs}}}}

***Value for {persona_name}:** {{{{Operational benefit}}}}*""",

                "governance_compliance": f"""# Governance & Compliance

*Audit-ready from day one*

## The Point

{{{{How compliance approach protects {persona_name}}}}}

## Regulatory Coverage

| Requirement | Our Approach | Evidence |
|-------------|--------------|----------|
| {{{{Reg 1}}}} | {{{{How we address}}}} | [Qdrant:T2] {{{{Proof}}}} |

## Certifications

- {{{{Cert 1}}}} - [Qdrant:T3] Validated
- {{{{Cert 2}}}} - [Qdrant:T3] Validated

## Risk Management

{{{{Proactive risk acknowledgment with mitigation}}}}

***Value for {persona_name}:** {{{{Compliance benefit}}}}*""",

                "implementation": f"""# Implementation & Transition

*Low-risk path to go-live*

## Timeline

| Phase | Duration | Milestone |
|-------|----------|-----------|
| Discovery | {{{{X weeks}}}} | {{{{Deliverable}}}} |
| Build | {{{{X weeks}}}} | {{{{Deliverable}}}} |
| Pilot | {{{{X weeks}}}} | {{{{Deliverable}}}} |
| Go-Live | {{{{Date}}}} | {{{{Success criteria}}}} |

## The Point

{{{{How transition approach minimizes risk for {persona_name}}}}}

## Risk Mitigation

**Challenge:** {{{{Honest risk acknowledgment}}}}
**Mitigation:** {{{{Specific actions}}}}

***Value for {persona_name}:** {{{{Transition benefit}}}}*""",
            }

            template = templates.get(section_type, f"""# {{{{Section Title}}}}

*{{{{Framing statement}}}}*

| Metric | Metric | Metric |
|--------|--------|--------|
| Value  | Value  | Value  |

## The Point

{{{{Why this matters to {persona_name}}}}}

## Detail

{{{{Content with [Source] attribution}}}}

***Value for {persona_name}:** {{{{Benefit statement}}}}*""")

            output = [
                f"# Response Template: {section_type.replace('_', ' ').title()}",
                "",
                f"**Persona:** {persona_name}",
                "",
                "---",
                "",
                "## Template",
                "",
                "```markdown",
                template,
                "```",
                "",
                "---",
                "",
                "## Instructions",
                "",
                "1. Replace all `{{{{placeholders}}}}` with verified data",
                "2. Add `[Source]` attribution for every statistic",
                "3. Use `search_claims` to find Qdrant evidence",
                "4. Keep placeholders for unknown data - DON'T FABRICATE",
                "5. Run `check_for_fabrication` before finalizing"
            ]

            return "\n".join(output)

        elif name == "llm_fact_check":

            output = [
                "# LLM Fact-Check (Final Pass)",
                "",
                f"**Model:** {FACT_CHECK_MODEL}",
                f"**Content length:** {len(content)} characters",
                "",
                "---",
                ""
            ]

            try:
                # Build the prompt
                user_prompt = FACT_CHECK_USER_PROMPT.format(
                    content=content[:8000],  # Limit content size
                    evidence=evidence_summary[:2000]
                )

                full_prompt = f"{FACT_CHECK_SYSTEM_PROMPT}\n\n{user_prompt}"

                # Call Ollama (sync version using httpx)
                with httpx.Client(timeout=120.0) as client:
                    response = client.post(
                        OLLAMA_URL,
                        json={
                            "model": FACT_CHECK_MODEL,
                            "prompt": full_prompt,
                            "stream": False,
                            "options": {
                                "temperature": 0.1,  # Low temp for factual checking
                                "num_predict": 2000
                            }
                        }
                    )

                    if response.status_code == 200:
                        result = response.json()
                        llm_response = result.get("response", "No response from LLM")

                        output.extend([
                            "## LLM Analysis",
                            "",
                            llm_response,
                            "",
                            "---",
                            "",
                            "## Next Steps",
                            "",
                            "1. Fix all **Critical Issues** before using content",
                            "2. Review **Warnings** and add sources or placeholders",
                            "3. Re-run fact-check after fixes",
                            ""
                        ])
                    else:
                        output.extend([
                            "## ❌ LLM Error",
                            "",
                            f"Status: {response.status_code}",
                            f"Response: {response.text[:500]}",
                            "",
                            "Try again or use `check_for_fabrication` for regex-based check."
                        ])

            except Exception as e:
                output.extend([
                    "## ❌ Error",
                    "",
                    f"Could not complete fact-check: {str(e)}",
                    "",
                    "Ensure Ollama is running: `curl http://localhost:11434/api/tags`",
                    "",
                    "Fallback: Use `check_for_fabrication` for regex-based check."
                ])

            return "\n".join(output)

        elif name == "search_style_patterns":
            # Search PostgreSQL for Foundever voice model patterns
            template_type = arguments.get("template_type")
            category = arguments.get("category")
            keyword = arguments.get("keyword")
            limit = arguments.get("limit", 10)

            output = [
                "# Foundever Voice Model Patterns",
                "",
                "*Use these as style examples for RFP content generation*",
                ""
            ]

            try:
                conn = psycopg2.connect(**DB_CONFIG)
                cur = conn.cursor()

                # Build query
                conditions = []
                params = []

                if template_type:
                    conditions.append("template_type = %s")
                    params.append(template_type)

                if category:
                    conditions.append("category = %s")
                    params.append(category)

                if keyword:
                    conditions.append("template_text ILIKE %s")
                    params.append(f"%{keyword}%")

                where_clause = " AND ".join(conditions) if conditions else "1=1"
                params.append(limit)

                query = f"""
                    SELECT template_type, category, template_text, placeholders, source_client
                    FROM narrative_templates
                    WHERE {where_clause}
                    ORDER BY created_at DESC
                    LIMIT %s
                """

                cur.execute(query, params)
                rows = cur.fetchall()

                if not rows:
                    output.extend([
                        "## No Patterns Found",
                        "",
                        "The narrative_templates table may be empty.",
                        "Run the extraction pipeline first:",
                        "```",
                        "cd /home/willard/Downloads/k",
                        "python run_full_extraction.py",
                        "python build_training_dataset.py",
                        "```",
                        "",
                        "Or check the extraction status:",
                        "```sql",
                        "SELECT COUNT(*) FROM narrative_templates;",
                        "SELECT COUNT(*) FROM document_extractions;",
                        "```"
                    ])
                else:
                    # Group by type
                    by_type = {}
                    for row in rows:
                        ttype, cat, text, placeholders, client = row
                        if ttype not in by_type:
                            by_type[ttype] = []
                        by_type[ttype].append({
                            "text": text,
                            "category": cat,
                            "placeholders": placeholders or [],
                            "source": client
                        })

                    output.append(f"**Found {len(rows)} patterns**")
                    output.append("")

                    for ttype, patterns in by_type.items():
                        output.append(f"## {ttype.replace('_', ' ').title()}")
                        output.append("")

                        for i, p in enumerate(patterns, 1):
                            output.append(f"### Example {i}")
                            output.append(f"*Category: {p['category']} | Source: {p['source'] or 'Unknown'}*")
                            output.append("")
                            output.append("```")
                            output.append(p['text'])
                            output.append("```")
                            if p['placeholders']:
                                output.append(f"Placeholders: `{', '.join(p['placeholders'])}`")
                            output.append("")

                    output.extend([
                        "---",
                        "",
                        "## Usage Instructions",
                        "",
                        "1. **Adapt patterns** to your specific client context",
                        "2. **Replace placeholders** with actual values or {{Client_Name}} style",
                        "3. **Maintain structure** - the linguistic flow is the key",
                        "4. **Combine patterns** - use confirmation → value bridge → so-what close",
                        ""
                    ])

                conn.close()

            except Exception as e:
                output.extend([
                    "## ❌ Database Error",
                    "",
                    f"Could not connect to PostgreSQL: {str(e)}",
                    "",
                    "Check connection settings in config.py:",
                    "```python",
                    f"DB_CONFIG = {DB_CONFIG}",
                    "```"
                ])

            return "\n".join(output)

        elif name == "generate_rfp_response":
            # Generate RFP response using fine-tuned Foundever voice model
            requirement = arguments["requirement"]
            context = arguments.get("context", "")
            section_type = arguments.get("section_type", "general")

            output = [
                "# Foundever Voice Model Response",
                "",
                f"*Section Type: {section_type}*",
                "",
                "---",
                ""
            ]

            try:
                # Build prompt with section context
                section_prompts = {
                    "executive_summary": "Write an executive summary RFP response",
                    "solution_approach": "Write a solution approach section",
                    "staffing": "Write a staffing and workforce section",
                    "technology": "Write a technology capabilities section",
                    "compliance": "Write a compliance and governance section",
                    "pricing_intro": "Write a pricing methodology introduction (no specific prices)",
                    "general": "Write an RFP response"
                }

                prompt = f"{section_prompts.get(section_type, 'Write an RFP response')} for this requirement:\n\n\"{requirement}\""

                if context:
                    prompt += f"\n\nAdditional context: {context}"

                prompt += "\n\nRespond in Foundever's professional voice with confirmation syntax, value bridges, and so-what closes."

                # Call Ollama with foundever-voice model
                async with httpx.AsyncClient(timeout=120.0) as client:
                    response = await client.post(
                        OLLAMA_URL,
                        json={
                            "model": FOUNDEVER_VOICE_MODEL,
                            "prompt": prompt,
                            "system": FOUNDEVER_VOICE_SYSTEM_PROMPT,
                            "stream": False,
                            "options": {
                                "temperature": 0.3,
                                "top_p": 0.9
                            }
                        }
                    )

                    if response.status_code == 200:
                        result = response.json()
                        generated_text = result.get("response", "")

                        output.append("## Generated Response")
                        output.append("")
                        output.append(generated_text)
                        output.append("")
                        output.append("---")
                        output.append("")
                        output.append("## Usage Notes")
                        output.append("")
                        output.append("1. **Fill placeholders** - Replace `{{...}}` with actual client data")
                        output.append("2. **Verify claims** - Use `fact_check_content` tool to validate")
                        output.append("3. **Enrich with evidence** - Use `search_claims` to find supporting data")
                        output.append("")
                        output.append(f"*Generated by: {FOUNDEVER_VOICE_MODEL}*")
                    else:
                        output.append(f"## ❌ Ollama Error")
                        output.append("")
                        output.append(f"Status: {response.status_code}")
                        output.append(f"Response: {response.text[:500]}")

            except Exception as e:
                output.extend([
                    "## ❌ Generation Error",
                    "",
                    f"Could not generate response: {str(e)}",
                    "",
                    "Ensure Ollama is running with foundever-voice model:",
                    "```bash",
                    "ollama list | grep foundever",
                    "```"
                ])

            return "\n".join(output)

        else:
            return f"Unknown tool: {name}"

    except Exception as e:
        logger.exception(f"Error handling tool {name}")
        return f"Error: {str(e)}"


# Create MCP Server
mcp_server = Server("style-guide-enrichment")


@mcp_server.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools."""
    return TOOLS + DOCUMENT_TOOLS


@mcp_server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool calls."""
    result = await handle_tool_call(name, arguments or {})
    return [TextContent(type="text", text=result)]


# HTTP/SSE Server for remote access
def create_sse_app():
    """Create Starlette app with SSE transport."""
    # SSE transport needs a relative endpoint for POST messages
    sse_transport = SseServerTransport("/mcp/messages")

    async def handle_sse_get(request):
        """Handle GET request to establish SSE connection."""
        async with sse_transport.connect_sse(
            request.scope, request.receive, request._send
        ) as streams:
            await mcp_server.run(
                streams[0], streams[1], mcp_server.create_initialization_options()
            )

    async def handle_sse_post(request):
        """Handle POST request for client messages."""
        await sse_transport.handle_post_message(
            request.scope, request.receive, request._send
        )

    async def handle_health(request):
        return JSONResponse({
            "status": "ok",
            "server": "style-guide-enrichment",
            "tools": len(TOOLS) + len(DOCUMENT_TOOLS),
            "style_guide_tools": len(TOOLS),
            "document_tools": len(DOCUMENT_TOOLS),
            "personas": len(CLIENT_PERSONAS),
            "domains": len(BUYER_DOMAIN_TAXONOMY)
        })

    async def handle_info(request):
        return JSONResponse({
            "name": "Style Guide Enrichment MCP Server",
            "version": "1.1.0",
            "description": "Enriches Foundever RFP style guides with Qdrant evidence. Includes document skills (PDF, XLSX, DOCX, PPTX).",
            "tools": [t.name for t in TOOLS + DOCUMENT_TOOLS],
            "document_tools": [t.name for t in DOCUMENT_TOOLS],
            "personas": list(CLIENT_PERSONAS.keys()),
            "domains": list(BUYER_DOMAIN_TAXONOMY.keys()),
            "mcp_endpoint": "/mcp/messages"
        })

    async def handle_tool_rest(request):
        """Direct REST endpoint for tool calls (convenience wrapper)."""
        from starlette.responses import PlainTextResponse
        try:
            body = await request.json()
            tool_name = request.path_params.get("tool_name")
            result = await handle_tool_call(tool_name, body)
            return PlainTextResponse(result, media_type="text/markdown")
        except Exception as e:
            return PlainTextResponse(f"Error: {str(e)}", status_code=500)

    routes = [
        Route("/mcp/messages", endpoint=handle_sse_get, methods=["GET"]),
        Route("/mcp/messages", endpoint=handle_sse_post, methods=["POST"]),
        Route("/tools/{tool_name}", endpoint=handle_tool_rest, methods=["POST"]),
        Route("/health", endpoint=handle_health),
        Route("/", endpoint=handle_info),
    ]

    return Starlette(routes=routes)


def run_stdio():
    """Run MCP server over stdio (for local Claude Desktop)."""
    logger.info("Starting MCP server in stdio mode")

    # Pre-load all models before starting server
    logger.info("")
    logger.info("Pre-loading models (this may take 10-30 seconds)...")
    init_models()
    logger.info("")

    logger.info("Starting stdio server...")
    asyncio.run(stdio_server(mcp_server))


def run_http(host: str = "0.0.0.0", port: int = 8420):
    """Run MCP server over HTTP/SSE (for remote access)."""
    logger.info(f"Starting MCP server on http://{host}:{port}")
    logger.info(f"MCP endpoint: http://{host}:{port}/mcp/messages")
    logger.info(f"Health check: http://{host}:{port}/health")

    # Pre-load all models before starting server
    logger.info("")
    logger.info("Pre-loading models (this may take 10-30 seconds)...")
    init_models()
    logger.info("")

    # Create app and start server
    app = create_sse_app()
    logger.info("Starting HTTP server...")
    uvicorn.run(app, host=host, port=port, log_level="info")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--stdio":
        run_stdio()
    else:
        # Default to HTTP server
        port = int(sys.argv[1]) if len(sys.argv) > 1 else 8420
        run_http(port=port)
