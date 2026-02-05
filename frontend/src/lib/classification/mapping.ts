/**
 * FE → Backend Section Mapping
 * =============================
 * Maps the FE classification taxonomy (Layer 2 primary labels) to the
 * MCP server's canonical 9-section proposal structure.
 *
 * The backend structure (from map_to_style_guide_structure) is:
 *   1. Executive Summary
 *   2. Understanding Client Needs
 *   3. Solution Overview
 *   4. Delivery Model
 *   5. Technology & Innovation
 *   6. Governance & Compliance
 *   7. Implementation & Transition
 *   8. Team & Leadership
 *   9. Proof Points & Evidence
 *
 * FE labels are BROADER than backend sections. A single FE label like
 * "operational_details" fans out across multiple backend sections.
 * The mapping is many-to-many with a primary affinity.
 */

import type { PrimaryLabel, BackendSection, IntentGroup } from "./types";

// ---------------------------------------------------------------------------
// Primary label → backend section mapping
// ---------------------------------------------------------------------------

export interface SectionMapping {
  /** The primary backend section this label maps to */
  primary: BackendSection;
  /** Additional backend sections this content may contribute to */
  secondary: BackendSection[];
  /** How to use this content in the proposal */
  usage: string;
}

/**
 * Maps each FE primary label to backend proposal section(s).
 *
 * Key design decision: "operational_details" is the largest FE bucket (~47%)
 * and fans out across 4 backend sections. This is intentional — the FE
 * classifier groups broadly, and the backend mapping disambiguates by
 * content signals during requirement extraction.
 */
export const LABEL_TO_SECTIONS: Record<PrimaryLabel, SectionMapping> = {
  executive_summary: {
    primary: "executive_summary",
    secondary: ["client_understanding"],
    usage:
      "Direct mapping. Use 1-Plus structure: lead with operational baseline, then included value.",
  },

  solution_overview: {
    primary: "solution_overview",
    secondary: ["technology", "delivery_model"],
    usage:
      "High-level capabilities go to solution_overview. Technology specifics split to technology section. Delivery architecture splits to delivery_model.",
  },

  operational_details: {
    primary: "delivery_model",
    secondary: ["team_leadership", "solution_overview", "technology"],
    usage:
      "The broadest FE label. Staffing/FTE/site → delivery_model. Org charts/leadership → team_leadership. Process/workflow → solution_overview. Tools/platforms → technology.",
  },

  case_study: {
    primary: "proof_points",
    secondary: ["client_understanding"],
    usage:
      "Primary home is proof_points. Client-specific insights can also inform client_understanding framing.",
  },

  compliance_security: {
    primary: "governance_compliance",
    secondary: ["proof_points"],
    usage:
      "Direct mapping. Certifications and audit results can also serve as proof_points evidence.",
  },

  project_plan: {
    primary: "implementation",
    secondary: ["delivery_model"],
    usage:
      "Direct mapping. Transition timeline → implementation. Ongoing operational model → delivery_model.",
  },

  pricing: {
    primary: "executive_summary",
    secondary: [],
    usage:
      "Pricing is NEVER included in proposal body per style guide rules. Flag for commercial appendix only. Executive summary may reference commercial model CONCEPT without numbers.",
  },

  other: {
    primary: "executive_summary",
    secondary: [],
    usage:
      "Section dividers and structural slides are navigation aids. Extract any actual content and reclassify. Otherwise discard.",
  },

  unclassified: {
    primary: "executive_summary",
    secondary: [],
    usage:
      "Low-confidence content. Surface for manual review. Do not auto-assign to proposal sections.",
  },
};

// ---------------------------------------------------------------------------
// Intent group → backend section mapping (coarser routing)
// ---------------------------------------------------------------------------

export const INTENT_TO_SECTIONS: Record<IntentGroup, BackendSection[]> = {
  narrative_positioning: ["executive_summary", "client_understanding", "solution_overview"],
  solution_definition: ["solution_overview", "delivery_model", "technology"],
  execution_delivery: ["delivery_model", "implementation", "team_leadership"],
  risk_assurance: ["governance_compliance"],
  proof_validation: ["proof_points"],
  commercial_mechanics: [], // Pricing excluded from proposal body
  structural: [],
};

// ---------------------------------------------------------------------------
// Backend section definitions (matches MCP server's 9-section structure)
// ---------------------------------------------------------------------------

export interface BackendSectionDefinition {
  id: BackendSection;
  displayName: string;
  number: number;
  styleGuideNotes: string[];
  /** MCP tools to call for this section */
  mcpTools: string[];
}

export const BACKEND_SECTIONS: Record<BackendSection, BackendSectionDefinition> = {
  executive_summary: {
    id: "executive_summary",
    displayName: "Executive Summary",
    number: 1,
    styleGuideNotes: [
      "Lead with operational capability (what they asked for)",
      "Position value-adds as 'included, not required'",
      "No action required from client framing",
    ],
    mcpTools: [
      "get_response_template",
      "search_claims",
      "generate_rfp_response",
    ],
  },

  client_understanding: {
    id: "client_understanding",
    displayName: "Understanding Client Needs",
    number: 2,
    styleGuideNotes: [
      "Demonstrate understanding of their specific challenges",
      "Reference their industry/persona context",
      "Show you've read and understood the RFP",
    ],
    mcpTools: [
      "get_response_template",
      "search_by_persona",
      "get_finserv_persona",
    ],
  },

  solution_overview: {
    id: "solution_overview",
    displayName: "Solution Overview",
    number: 3,
    styleGuideNotes: [
      "High-level solution architecture",
      "How it addresses stated requirements",
      "Differentiation without explicit competitor mentions",
    ],
    mcpTools: [
      "get_response_template",
      "search_claims",
      "get_solution_options",
      "enrich_section",
    ],
  },

  delivery_model: {
    id: "delivery_model",
    displayName: "Delivery Model",
    number: 4,
    styleGuideNotes: [
      "Site strategy and rationale",
      "FTE model and staffing approach",
      "Hours of operation and coverage",
    ],
    mcpTools: [
      "get_response_template",
      "search_claims",
      "enrich_section",
    ],
  },

  technology: {
    id: "technology",
    displayName: "Technology & Innovation",
    number: 5,
    styleGuideNotes: [
      "Platform capabilities",
      "Integration approach",
      "AI/automation where applicable",
    ],
    mcpTools: [
      "get_response_template",
      "search_claims",
      "enrich_section",
    ],
  },

  governance_compliance: {
    id: "governance_compliance",
    displayName: "Governance & Compliance",
    number: 6,
    styleGuideNotes: [
      "Regulatory framework coverage",
      "Certifications and audits",
      "Risk management approach",
    ],
    mcpTools: [
      "get_response_template",
      "search_claims",
      "get_threat_context",
      "check_content_compliance",
    ],
  },

  implementation: {
    id: "implementation",
    displayName: "Implementation & Transition",
    number: 7,
    styleGuideNotes: [
      "Timeline with milestones",
      "Risk mitigation for transition",
      "Training and ramp approach",
    ],
    mcpTools: [
      "get_response_template",
      "search_claims",
      "enrich_section",
    ],
  },

  team_leadership: {
    id: "team_leadership",
    displayName: "Team & Leadership",
    number: 8,
    styleGuideNotes: [
      "Proposed leadership structure",
      "Account management model",
      "Escalation paths",
    ],
    mcpTools: [
      "get_response_template",
      "search_claims",
    ],
  },

  proof_points: {
    id: "proof_points",
    displayName: "Proof Points & Evidence",
    number: 9,
    styleGuideNotes: [
      "Relevant case studies (use personas, not names)",
      "Metrics from similar programs",
      "Third-party validation",
    ],
    mcpTools: [
      "get_response_template",
      "search_claims",
      "validate_claim",
      "get_foundever_evidence",
    ],
  },
};

// ---------------------------------------------------------------------------
// Resolve: given a classification result, return ordered backend sections
// ---------------------------------------------------------------------------

export function resolveBackendSections(
  primaryLabel: PrimaryLabel,
): BackendSection[] {
  const mapping = LABEL_TO_SECTIONS[primaryLabel];
  if (!mapping) return ["executive_summary"];
  return [mapping.primary, ...mapping.secondary];
}

/**
 * Given extracted text and its primary label, refine to a single best
 * backend section using keyword signals.
 *
 * This handles the "operational_details" fan-out problem: a slide labeled
 * "operational_details" could be about staffing (delivery_model),
 * org structure (team_leadership), or tools (technology).
 */
export function refineToSingleSection(
  primaryLabel: PrimaryLabel,
  text: string,
): BackendSection {
  const mapping = LABEL_TO_SECTIONS[primaryLabel];
  if (!mapping) return "executive_summary";

  // If no secondary sections, use primary
  if (mapping.secondary.length === 0) return mapping.primary;

  const lowerText = text.toLowerCase();

  // Refinement signals for operational_details (the big bucket)
  if (primaryLabel === "operational_details") {
    const signals: [string[], BackendSection][] = [
      [["org chart", "leadership", "escalation", "account manager", "director", "VP"], "team_leadership"],
      [["platform", "tool", "software", "CRM", "telephony", "IVR", "API", "AI", "automation"], "technology"],
      [["FTE", "staffing", "site", "headcount", "shift", "roster", "capacity", "facility"], "delivery_model"],
      [["process", "workflow", "SOP", "procedure"], "solution_overview"],
    ];

    for (const [keywords, section] of signals) {
      const hits = keywords.filter((kw) => lowerText.includes(kw.toLowerCase()));
      if (hits.length >= 2) return section;
    }
  }

  // Refinement signals for solution_overview
  if (primaryLabel === "solution_overview") {
    const techSignals = ["platform", "integration", "API", "AI", "machine learning", "analytics"];
    const techHits = techSignals.filter((kw) => lowerText.includes(kw.toLowerCase()));
    if (techHits.length >= 2) return "technology";
  }

  return mapping.primary;
}
