#!/usr/bin/env python3
"""
PPTX & Slide Library MCP Tools
================================
MCP tool definitions and handlers for PPTX generation and slide library management.

Provides 8 new tools:
  1. index_slide_library     — Scan and index a theme-organized slide library
  2. search_slide_library    — Search slides by keyword, theme, label, or section
  3. get_slide_library_stats — Get library overview (themes, distributions)
  4. analyze_pptx_template   — Inspect layouts and placeholders in a PPTX template
  5. create_proposal_deck    — Create a new proposal deck (blank or from template)
  6. add_proposal_slide      — Add a content slide to the active deck
  7. clone_library_slide     — Clone a slide from the library into the active deck
  8. save_proposal_deck      — Save the assembled deck to disk

These tools integrate with the existing 33 MCP tools, extending the system from
content generation to deliverable assembly.
"""

import json
import logging
from typing import Any, Dict, List, Optional

from mcp.types import Tool

logger = logging.getLogger("pptx-tools")

# ---------------------------------------------------------------------------
# Module-level state for the active deck builder
# ---------------------------------------------------------------------------

_active_builder = None


def _get_builder():
    global _active_builder
    return _active_builder


def _set_builder(builder):
    global _active_builder
    _active_builder = builder


# ---------------------------------------------------------------------------
# Tool definitions
# ---------------------------------------------------------------------------

PPTX_TOOLS = [
    # Slide Library tools
    Tool(
        name="index_slide_library",
        description="""Scan and index a theme-organized slide library directory.

The library should be organized as:
  library_root/
    Theme Name/
      slide.pptx + slide.txt (OCR text)
    Another Theme/
      ...

Returns: theme count, slide count, label and section distributions.
Automatically classifies each slide to the 3-layer taxonomy and maps to backend sections.""",
        inputSchema={
            "type": "object",
            "properties": {
                "library_path": {
                    "type": "string",
                    "description": "Absolute path to the slide library root directory"
                }
            },
            "required": ["library_path"]
        }
    ),

    Tool(
        name="search_slide_library",
        description="""Search the indexed slide library by keyword query.

Supports filtering by theme name, primary label (executive_summary, solution_overview,
operational_details, case_study, compliance_security, project_plan), or backend section
(executive_summary, delivery_model, technology, etc.).

Returns matching slides with OCR text excerpts and classification info.""",
        inputSchema={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query (keywords to match against slide OCR text)"
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum results to return (default: 10)",
                    "default": 10
                },
                "theme_filter": {
                    "type": "string",
                    "description": "Filter to a specific theme folder name"
                },
                "label_filter": {
                    "type": "string",
                    "description": "Filter to a primary label",
                    "enum": [
                        "executive_summary", "solution_overview", "operational_details",
                        "case_study", "compliance_security", "project_plan",
                        "pricing", "other", "unclassified"
                    ]
                },
                "section_filter": {
                    "type": "string",
                    "description": "Filter to a backend section",
                    "enum": [
                        "executive_summary", "client_understanding", "solution_overview",
                        "delivery_model", "technology", "governance_compliance",
                        "implementation", "team_leadership", "proof_points"
                    ]
                }
            },
            "required": ["query"]
        }
    ),

    Tool(
        name="get_slide_library_stats",
        description="""Get overview statistics for the indexed slide library.

Returns: total slides, total themes, per-theme breakdown with label and section
distributions. Useful for understanding what reference material is available
before building a proposal deck.""",
        inputSchema={
            "type": "object",
            "properties": {},
        }
    ),

    # PPTX Builder tools
    Tool(
        name="analyze_pptx_template",
        description="""Analyze a PPTX or POTX template to discover its slide layouts and placeholders.

Returns layout names, placeholder indices, types (title, body, chart, etc.),
and positions. Run this before populating slides to understand what
placeholders are available.

Cross-platform equivalent of powerpoint-mcp's analyze_template (no COM/Windows required).""",
        inputSchema={
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Path to .pptx or .potx template file"
                }
            },
            "required": ["file_path"]
        }
    ),

    Tool(
        name="create_proposal_deck",
        description="""Create a new proposal deck, either blank or from an existing template.

If template_path is provided, the deck inherits all slide masters, layouts,
themes, and fonts from the template. The template is analyzed automatically
and layout information is returned.

Optionally adds a title slide with the provided title and subtitle.

The created deck becomes the 'active deck' for subsequent add_proposal_slide
and clone_library_slide calls.""",
        inputSchema={
            "type": "object",
            "properties": {
                "template_path": {
                    "type": "string",
                    "description": "Path to .pptx/.potx template (optional, creates blank deck if omitted)"
                },
                "title": {
                    "type": "string",
                    "description": "Title for the cover slide (optional)"
                },
                "subtitle": {
                    "type": "string",
                    "description": "Subtitle for the cover slide (optional)"
                }
            }
        }
    ),

    Tool(
        name="add_proposal_slide",
        description="""Add a content slide to the active proposal deck.

Populates the slide with title, body content, optional table data,
and speaker notes for traceability. Body content supports HTML-like
formatting tags: <b>bold</b>, <i>italic</i>, <u>underline</u>, <br>.

Speaker notes are used to attach evidence claim IDs, proof tier info,
and source URLs for reviewer audit trails.

section_type maps to the backend 9-section structure for tracking
which proposal sections have been populated.""",
        inputSchema={
            "type": "object",
            "properties": {
                "section_type": {
                    "type": "string",
                    "description": "Backend section this slide belongs to",
                    "enum": [
                        "executive_summary", "client_understanding", "solution_overview",
                        "delivery_model", "technology", "governance_compliance",
                        "implementation", "team_leadership", "proof_points"
                    ]
                },
                "title": {
                    "type": "string",
                    "description": "Slide title"
                },
                "body": {
                    "type": "string",
                    "description": "Body content (supports <b>, <i>, <u>, <br> tags)"
                },
                "speaker_notes": {
                    "type": "string",
                    "description": "Speaker notes for traceability (evidence IDs, sources)"
                },
                "table_data": {
                    "type": "array",
                    "description": "Optional table data as 2D array [[header1, header2], [val1, val2]]",
                    "items": {
                        "type": "array",
                        "items": {"type": "string"}
                    }
                },
                "add_divider": {
                    "type": "boolean",
                    "description": "Add a section divider slide before this content (default: false)",
                    "default": False
                }
            },
            "required": ["section_type", "title", "body"]
        }
    ),

    Tool(
        name="clone_library_slide",
        description="""Clone a slide from the indexed slide library into the active proposal deck.

Uses the slide's PPTX file path and index to copy it into the current deck.
Preserves shapes, text, and basic formatting. Optionally appends speaker
notes for traceability.

Use search_slide_library first to find the slide you want to clone.""",
        inputSchema={
            "type": "object",
            "properties": {
                "slide_id": {
                    "type": "string",
                    "description": "Slide ID from search results (e.g., 'slide_0042')"
                },
                "source_slide_index": {
                    "type": "integer",
                    "description": "Which slide within the source file to clone (0-indexed, default: 0)",
                    "default": 0
                },
                "speaker_notes": {
                    "type": "string",
                    "description": "Additional speaker notes to append"
                }
            },
            "required": ["slide_id"]
        }
    ),

    Tool(
        name="save_proposal_deck",
        description="""Save the active proposal deck to disk.

Returns the saved file path and a build summary showing which sections
have been added and which are still missing.

Output format is .pptx. The directory is created if it doesn't exist.""",
        inputSchema={
            "type": "object",
            "properties": {
                "output_path": {
                    "type": "string",
                    "description": "Path to save the .pptx file (e.g., 'output/proposal.pptx')"
                }
            },
            "required": ["output_path"]
        }
    ),
]


# ---------------------------------------------------------------------------
# Tool handlers
# ---------------------------------------------------------------------------

async def handle_pptx_tool(name: str, arguments: Dict[str, Any]) -> Optional[str]:
    """
    Handle PPTX and slide library tool calls.

    Returns None if the tool name is not a PPTX tool (pass-through pattern
    matching document_tools.py).
    """

    # ----- Slide Library Tools -----

    if name == "index_slide_library":
        return _handle_index_slide_library(arguments)

    elif name == "search_slide_library":
        return _handle_search_slide_library(arguments)

    elif name == "get_slide_library_stats":
        return _handle_get_slide_library_stats(arguments)

    # ----- PPTX Builder Tools -----

    elif name == "analyze_pptx_template":
        return _handle_analyze_pptx_template(arguments)

    elif name == "create_proposal_deck":
        return _handle_create_proposal_deck(arguments)

    elif name == "add_proposal_slide":
        return _handle_add_proposal_slide(arguments)

    elif name == "clone_library_slide":
        return _handle_clone_library_slide(arguments)

    elif name == "save_proposal_deck":
        return _handle_save_proposal_deck(arguments)

    return None  # Not a PPTX tool


# ---------------------------------------------------------------------------
# Handler implementations
# ---------------------------------------------------------------------------

def _handle_index_slide_library(arguments: Dict[str, Any]) -> str:
    from slide_library import set_slide_library_path

    library_path = arguments["library_path"]
    try:
        manager = set_slide_library_path(library_path)
        stats = manager.index()
        return json.dumps(stats, indent=2)
    except FileNotFoundError as e:
        return f"Error: {e}"
    except Exception as e:
        logger.exception("Error indexing slide library")
        return f"Error indexing slide library: {e}"


def _handle_search_slide_library(arguments: Dict[str, Any]) -> str:
    from slide_library import get_slide_library

    try:
        manager = get_slide_library()
    except ValueError:
        return "Error: No slide library indexed. Call index_slide_library first."

    results = manager.search(
        query=arguments["query"],
        limit=arguments.get("limit", 10),
        theme_filter=arguments.get("theme_filter"),
        label_filter=arguments.get("label_filter"),
        section_filter=arguments.get("section_filter"),
    )

    if not results:
        return "No slides found matching query."

    output = [f"Found {len(results)} matching slides:\n"]
    for i, r in enumerate(results, 1):
        s = r.slide
        ocr_excerpt = s.ocr_text[:200].replace("\n", " ") if s.ocr_text else "(no OCR text)"
        output.append(
            f"{i}. [{s.id}] Theme: {s.theme}\n"
            f"   File: {s.file_name} ({s.slide_count} slide{'s' if s.slide_count > 1 else ''})\n"
            f"   Label: {s.primary_label} → Section: {s.backend_section} "
            f"(confidence: {s.confidence})\n"
            f"   Score: {r.score} — {r.match_reason}\n"
            f"   Text: {ocr_excerpt}...\n"
        )

    return "\n".join(output)


def _handle_get_slide_library_stats(arguments: Dict[str, Any]) -> str:
    from slide_library import get_slide_library

    try:
        manager = get_slide_library()
    except ValueError:
        return "Error: No slide library indexed. Call index_slide_library first."

    stats = manager.get_library_stats()
    return json.dumps(stats, indent=2)


def _handle_analyze_pptx_template(arguments: Dict[str, Any]) -> str:
    from pptx_builder import analyze_template

    file_path = arguments["file_path"]
    try:
        analysis = analyze_template(file_path)
        result = analysis.to_dict()

        # Format for readability
        output = [f"Template: {file_path}"]
        output.append(f"Slide size: {result['slide_width']} x {result['slide_height']} EMU")
        output.append(f"Layouts: {result['layout_count']}\n")

        for layout in result["layouts"]:
            output.append(f"  Layout {layout['index']}: \"{layout['name']}\"")
            if layout["placeholders"]:
                for ph in layout["placeholders"]:
                    output.append(
                        f"    [{ph['idx']}] {ph['name']} "
                        f"({ph['placeholder_type']}) "
                        f"— {ph['width']}x{ph['height']} EMU"
                    )
            else:
                output.append("    (no placeholders)")
            output.append("")

        return "\n".join(output)
    except FileNotFoundError:
        return f"Error: Template file not found: {file_path}"
    except Exception as e:
        logger.exception("Error analyzing template")
        return f"Error analyzing template: {e}"


def _handle_create_proposal_deck(arguments: Dict[str, Any]) -> str:
    from pptx_builder import ProposalDeckBuilder

    builder = ProposalDeckBuilder()
    template_path = arguments.get("template_path")
    title = arguments.get("title")
    subtitle = arguments.get("subtitle")

    try:
        if template_path:
            analysis = builder.create_from_template(template_path)
            output = [f"Created deck from template: {template_path}"]
            output.append(f"Available layouts: {analysis.layout_count}")
            for layout in analysis.layouts:
                ph_names = [p.name for p in layout.placeholders]
                output.append(f"  [{layout.index}] \"{layout.name}\" — placeholders: {ph_names}")
        else:
            builder.create_blank()
            output = ["Created blank proposal deck"]

        if title:
            idx = builder.add_title_slide(title, subtitle)
            output.append(f"Added title slide at index {idx}")

        _set_builder(builder)
        output.append(f"\nDeck is now active ({builder.slide_count} slides)")
        return "\n".join(output)

    except Exception as e:
        logger.exception("Error creating proposal deck")
        return f"Error creating proposal deck: {e}"


def _handle_add_proposal_slide(arguments: Dict[str, Any]) -> str:
    from pptx_builder import SlideContent, TextSegment, parse_formatted_text

    builder = _get_builder()
    if not builder:
        return "Error: No active deck. Call create_proposal_deck first."

    section_type = arguments["section_type"]
    title = arguments["title"]
    body = arguments["body"]
    speaker_notes = arguments.get("speaker_notes")
    table_data = arguments.get("table_data")
    add_divider = arguments.get("add_divider", False)

    try:
        if add_divider:
            builder.add_section_divider(section_type)

        # Parse body text for formatting
        body_segments = parse_formatted_text(body)

        content = SlideContent(
            section_type=section_type,
            title=title,
            body_segments=body_segments,
            speaker_notes=speaker_notes,
            table_data=table_data,
        )

        idx = builder.add_section_slide(content)

        summary = builder.get_build_summary()
        return (
            f"Added slide at index {idx}: \"{title}\" (section: {section_type})\n"
            f"Deck now has {summary['slide_count']} slides\n"
            f"Sections added: {', '.join(summary['sections_added'])}\n"
            f"Sections missing: {', '.join(summary['sections_missing'])}"
        )

    except Exception as e:
        logger.exception("Error adding proposal slide")
        return f"Error adding proposal slide: {e}"


def _handle_clone_library_slide(arguments: Dict[str, Any]) -> str:
    from slide_library import get_slide_library

    builder = _get_builder()
    if not builder:
        return "Error: No active deck. Call create_proposal_deck first."

    slide_id = arguments["slide_id"]
    source_index = arguments.get("source_slide_index", 0)
    speaker_notes = arguments.get("speaker_notes")

    try:
        manager = get_slide_library()
    except ValueError:
        return "Error: No slide library indexed. Call index_slide_library first."

    # Find the slide by ID
    target_slide = None
    for slide in manager.slides:
        if slide.id == slide_id:
            target_slide = slide
            break

    if target_slide is None:
        return f"Error: Slide ID '{slide_id}' not found in library."

    try:
        idx = builder.add_slide_from_library(
            source_path=target_slide.pptx_path,
            source_slide_index=source_index,
            speaker_notes_append=speaker_notes,
        )

        return (
            f"Cloned slide from library: {target_slide.file_name} "
            f"(theme: {target_slide.theme})\n"
            f"Inserted at index {idx}\n"
            f"Deck now has {builder.slide_count} slides"
        )

    except Exception as e:
        logger.exception("Error cloning library slide")
        return f"Error cloning slide: {e}"


def _handle_save_proposal_deck(arguments: Dict[str, Any]) -> str:
    builder = _get_builder()
    if not builder:
        return "Error: No active deck. Call create_proposal_deck first."

    output_path = arguments["output_path"]

    try:
        saved_path = builder.save(output_path)
        summary = builder.get_build_summary()

        output = [f"Saved proposal deck: {saved_path}"]
        output.append(f"Total slides: {summary['slide_count']}")
        output.append(f"Sections included: {', '.join(summary['sections_added']) or '(none)'}")
        output.append(f"Sections missing: {', '.join(summary['sections_missing']) or '(none — all sections present)'}")

        return "\n".join(output)

    except Exception as e:
        logger.exception("Error saving proposal deck")
        return f"Error saving deck: {e}"
