/**
 * Classification Taxonomy
 * =======================
 * Canonical taxonomy derived from corpus analysis of ~1,000 RFP slides.
 *
 * This is the single source of truth for the FE classification model.
 * Numbers, labels, and hierarchy are grounded in the actual corpus data.
 */

import type {
  PrimaryLabel,
  IntentGroup,
  DomainOverlay,
  BackendSection,
} from "./types";

// ---------------------------------------------------------------------------
// Layer 2 — Primary Label Definitions
// ---------------------------------------------------------------------------

export interface LabelDefinition {
  id: PrimaryLabel;
  displayName: string;
  description: string;
  /** Corpus frequency: approximate % of ~1,000 slides */
  corpusFrequency: number;
  /** Approximate count in corpus */
  corpusCount: [number, number];
  /** Signal keywords for lightweight pre-classification */
  signalKeywords: string[];
  /** What this label absorbs (micro-labels folded in) */
  absorbs: string[];
}

export const PRIMARY_LABELS: Record<PrimaryLabel, LabelDefinition> = {
  operational_details: {
    id: "operational_details",
    displayName: "Operational Details",
    description:
      "How-it-works content: processes, workflows, scorecards, incentives, staffing, facilities, day-to-day execution. Intentionally broad — absorbs micro-labels.",
    corpusFrequency: 0.475,
    corpusCount: [430, 470],
    signalKeywords: [
      "process", "workflow", "staffing", "FTE", "scorecard", "incentive",
      "facility", "site", "operations", "schedule", "training", "ramp",
      "attrition", "absenteeism", "quality", "QA", "calibration",
      "workforce", "capacity", "headcount", "shift", "roster",
    ],
    absorbs: [
      "staffing_model", "workforce_management", "quality_assurance",
      "training_plan", "site_strategy", "incentive_structure",
      "day_in_the_life", "organizational_chart", "reporting_structure",
    ],
  },

  solution_overview: {
    id: "solution_overview",
    displayName: "Solution Overview",
    description:
      "Capabilities, service offerings, value propositions, platform/ecosystem summaries. Higher-level than operational details.",
    corpusFrequency: 0.21,
    corpusCount: [190, 210],
    signalKeywords: [
      "solution", "capability", "platform", "offering", "service",
      "value", "approach", "architecture", "ecosystem", "innovation",
      "technology", "digital", "AI", "automation", "integration",
    ],
    absorbs: [
      "technology_overview", "platform_capabilities", "innovation_roadmap",
      "digital_strategy", "service_catalog",
    ],
  },

  case_study: {
    id: "case_study",
    displayName: "Case Study",
    description:
      "Client examples (named or anonymized), outcomes, metrics, proof points. High-leverage retrieval targets — sparse but valuable.",
    corpusFrequency: 0.11,
    corpusCount: [95, 115],
    signalKeywords: [
      "case study", "client", "outcome", "result", "achieved", "delivered",
      "improved", "reduced", "increased", "partnership", "engagement",
      "program", "testimonial", "reference",
    ],
    absorbs: [
      "client_reference", "proof_point", "testimonial", "success_story",
      "past_performance",
    ],
  },

  compliance_security: {
    id: "compliance_security",
    displayName: "Compliance / Security",
    description:
      "Certifications, regulatory frameworks, risk controls, audit evidence, governance structures.",
    corpusFrequency: 0.07,
    corpusCount: [60, 75],
    signalKeywords: [
      "compliance", "regulatory", "certification", "SOC", "PCI", "HIPAA",
      "audit", "governance", "risk", "security", "CFPB", "GDPR",
      "Reg E", "TCPA", "FDCPA", "control", "framework",
    ],
    absorbs: [
      "security_overview", "regulatory_compliance", "audit_results",
      "certification_list", "risk_management", "data_privacy",
    ],
  },

  project_plan: {
    id: "project_plan",
    displayName: "Project Plan",
    description:
      "Implementation, transition, PMO views, timelines, milestones, go-live planning.",
    corpusFrequency: 0.055,
    corpusCount: [45, 55],
    signalKeywords: [
      "implementation", "transition", "timeline", "milestone", "phase",
      "go-live", "PMO", "project plan", "ramp", "parallel", "cutover",
      "migration", "wave", "tranche",
    ],
    absorbs: [
      "transition_plan", "implementation_timeline", "pmo_structure",
      "go_live_criteria", "migration_plan",
    ],
  },

  executive_summary: {
    id: "executive_summary",
    displayName: "Executive Summary",
    description:
      'High-level framing, "1-pager logic", strategic overview, highlights. Rare but critical — sets the narrative.',
    corpusFrequency: 0.045,
    corpusCount: [40, 50],
    signalKeywords: [
      "executive summary", "overview", "highlights", "strategic",
      "partnership", "why us", "at a glance", "key differentiators",
      "summary", "introduction",
    ],
    absorbs: [
      "cover_letter", "introduction", "why_foundever", "key_highlights",
    ],
  },

  pricing: {
    id: "pricing",
    displayName: "Pricing",
    description:
      "Commercials, assumptions, cost treatment. Often orthogonal — appears as a flag rather than the sole primary label.",
    corpusFrequency: 0.0,
    corpusCount: [0, 0],
    signalKeywords: [
      "pricing", "cost", "rate", "commercial", "FTE cost", "hourly",
      "budget", "savings", "ROI", "investment",
    ],
    absorbs: [
      "pricing_model", "commercial_terms", "cost_assumptions",
      "rate_card",
    ],
  },

  other: {
    id: "other",
    displayName: "Other",
    description:
      "Section dividers, welcome slides, transitional rhetoric. Low semantic payload.",
    corpusFrequency: 0.035,
    corpusCount: [30, 40],
    signalKeywords: [
      "agenda", "table of contents", "section", "divider", "welcome",
      "thank you", "next steps", "appendix",
    ],
    absorbs: [
      "section_header", "divider_slide", "appendix_cover", "toc",
    ],
  },

  unclassified: {
    id: "unclassified",
    displayName: "Unclassified / Low Confidence",
    description:
      "Rare — usually due to missing content, placeholders, or slides with only images.",
    corpusFrequency: 0.01,
    corpusCount: [0, 10],
    signalKeywords: [],
    absorbs: [],
  },
};

// ---------------------------------------------------------------------------
// Layer 1 — Intent Group Definitions
// ---------------------------------------------------------------------------

export interface IntentGroupDefinition {
  id: IntentGroup;
  displayName: string;
  description: string;
  /** Which primary labels belong to this group */
  memberLabels: PrimaryLabel[];
}

export const INTENT_GROUPS: Record<IntentGroup, IntentGroupDefinition> = {
  narrative_positioning: {
    id: "narrative_positioning",
    displayName: "Narrative & Positioning",
    description: "Why us — executive framing and high-level solution story",
    memberLabels: ["executive_summary", "solution_overview"],
  },
  solution_definition: {
    id: "solution_definition",
    displayName: "Solution Definition",
    description: "What we deliver — capabilities and operational model",
    memberLabels: ["solution_overview", "operational_details"],
  },
  execution_delivery: {
    id: "execution_delivery",
    displayName: "Execution & Delivery",
    description: "How we deliver — operations, transition, timeline",
    memberLabels: ["operational_details", "project_plan"],
  },
  risk_assurance: {
    id: "risk_assurance",
    displayName: "Risk & Assurance",
    description: "Trust signals — compliance, security, governance",
    memberLabels: ["compliance_security"],
  },
  proof_validation: {
    id: "proof_validation",
    displayName: "Proof & Validation",
    description: "Evidence — case studies, outcomes, metrics",
    memberLabels: ["case_study"],
  },
  commercial_mechanics: {
    id: "commercial_mechanics",
    displayName: "Commercial Mechanics",
    description: "Pricing, commercial assumptions, cost treatment",
    memberLabels: ["pricing"],
  },
  structural: {
    id: "structural",
    displayName: "Structural / Transitional",
    description: "Section headers, dividers, navigation slides",
    memberLabels: ["other", "unclassified"],
  },
};

// ---------------------------------------------------------------------------
// Layer 3 — Domain Overlay Definitions
// ---------------------------------------------------------------------------

export interface DomainDefinition {
  id: DomainOverlay;
  displayName: string;
  signalKeywords: string[];
}

export const DOMAIN_OVERLAYS: Record<DomainOverlay, DomainDefinition> = {
  financial_services: {
    id: "financial_services",
    displayName: "Financial Services",
    signalKeywords: [
      "financial services", "finserv", "banking", "insurance",
      "capital markets", "wealth management",
    ],
  },
  banking: {
    id: "banking",
    displayName: "Banking",
    signalKeywords: [
      "bank", "retail bank", "deposits", "loans", "mortgage",
      "credit card", "checking", "savings", "branch",
    ],
  },
  fintech: {
    id: "fintech",
    displayName: "FinTech",
    signalKeywords: [
      "fintech", "digital lending", "neobank", "BNPL",
      "digital wallet", "embedded finance",
    ],
  },
  payments: {
    id: "payments",
    displayName: "Payments",
    signalKeywords: [
      "payment", "merchant", "transaction", "POS", "acquiring",
      "issuing", "card network", "settlement",
    ],
  },
  fraud_aml_kyc: {
    id: "fraud_aml_kyc",
    displayName: "Fraud / AML / KYC",
    signalKeywords: [
      "fraud", "AML", "KYC", "CDD", "SAR", "suspicious",
      "money laundering", "identity verification", "OFAC",
    ],
  },
  collections: {
    id: "collections",
    displayName: "Collections",
    signalKeywords: [
      "collections", "debt", "recovery", "RPC", "PTP",
      "liquidation", "skip tracing", "settlement", "default",
    ],
  },
  insurance: {
    id: "insurance",
    displayName: "Insurance",
    signalKeywords: [
      "insurance", "claims", "FNOL", "policy", "underwriting",
      "premium", "coverage", "carrier",
    ],
  },
  healthcare: {
    id: "healthcare",
    displayName: "Healthcare",
    signalKeywords: [
      "healthcare", "patient", "clinical", "HIPAA", "provider",
      "payer", "pharmacy", "health plan",
    ],
  },
  general: {
    id: "general",
    displayName: "General / Cross-Industry",
    signalKeywords: [],
  },
};

// ---------------------------------------------------------------------------
// Utility: get intent group for a primary label
// ---------------------------------------------------------------------------

const _labelToIntentGroup = new Map<PrimaryLabel, IntentGroup>();
for (const [groupId, group] of Object.entries(INTENT_GROUPS)) {
  for (const label of group.memberLabels) {
    // First match wins — some labels appear in multiple groups.
    // The earlier group in the object is the "primary" intent group.
    if (!_labelToIntentGroup.has(label)) {
      _labelToIntentGroup.set(label, groupId as IntentGroup);
    }
  }
}

export function getIntentGroup(label: PrimaryLabel): IntentGroup {
  return _labelToIntentGroup.get(label) ?? "structural";
}
