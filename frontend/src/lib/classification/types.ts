/**
 * Classification Types
 * ====================
 * TypeScript types for the 3-layer document classification hierarchy.
 * Derived from corpus analysis of ~1,000 RFP proposal slides.
 *
 * Layer 1: Intent Groups (FE routing)
 * Layer 2: Primary Labels (classifier output — the core taxonomy)
 * Layer 3: Overlays (secondary attributes: domain, pricing flag, confidence)
 */

// ---------------------------------------------------------------------------
// Layer 2 — Primary Labels (classifier output, authoritative)
// ---------------------------------------------------------------------------

export type PrimaryLabel =
  | "executive_summary"
  | "solution_overview"
  | "operational_details"
  | "case_study"
  | "compliance_security"
  | "project_plan"
  | "pricing"
  | "other"
  | "unclassified";

// ---------------------------------------------------------------------------
// Layer 1 — Intent Groups (FE routing, derived from label clusters)
// ---------------------------------------------------------------------------

export type IntentGroup =
  | "narrative_positioning"
  | "solution_definition"
  | "execution_delivery"
  | "risk_assurance"
  | "proof_validation"
  | "commercial_mechanics"
  | "structural";

// ---------------------------------------------------------------------------
// Layer 3 — Overlays (secondary attributes, not primary categories)
// ---------------------------------------------------------------------------

export type DomainOverlay =
  | "financial_services"
  | "banking"
  | "fintech"
  | "payments"
  | "fraud_aml_kyc"
  | "collections"
  | "insurance"
  | "healthcare"
  | "general";

export type PricingFlag = "has_pricing" | "pricing_adjacent" | "no_pricing";

export type ConfidenceLevel = "high" | "medium" | "low";

// ---------------------------------------------------------------------------
// Backend section types (MCP server's canonical 9-section structure)
// ---------------------------------------------------------------------------

export type BackendSection =
  | "executive_summary"
  | "client_understanding"
  | "solution_overview"
  | "delivery_model"
  | "technology"
  | "governance_compliance"
  | "implementation"
  | "team_leadership"
  | "proof_points";

// ---------------------------------------------------------------------------
// Classification result — what the FE classifier produces per document/slide
// ---------------------------------------------------------------------------

export interface ClassificationResult {
  /** Layer 2: Primary label from the classifier */
  primaryLabel: PrimaryLabel;

  /** Layer 1: Intent group (derived from primary label) */
  intentGroup: IntentGroup;

  /** Layer 3: Domain overlay */
  domain: DomainOverlay;

  /** Layer 3: Pricing flag (orthogonal to primary label) */
  pricingFlag: PricingFlag;

  /** Classifier confidence 0-1 */
  confidence: number;

  /** Confidence bucket */
  confidenceLevel: ConfidenceLevel;

  /** Backend section(s) this maps to */
  backendSections: BackendSection[];

  /** Secondary labels if content spans categories */
  secondaryLabels: PrimaryLabel[];
}

// ---------------------------------------------------------------------------
// Document-level types
// ---------------------------------------------------------------------------

export type DocumentType = "rfp" | "rfi" | "orals" | "addendum" | "past_proposal" | "score_sheet" | "compliance_matrix" | "unknown";

export type FileFormat = "pdf" | "docx" | "xlsx" | "pptx";

export interface DocumentMetadata {
  id: string;
  fileName: string;
  fileFormat: FileFormat;
  documentType: DocumentType;
  uploadedAt: string;
  pageCount: number;
  slideCount?: number;
  wordCount?: number;
}

export interface ClassifiedDocument extends DocumentMetadata {
  /** Per-page or per-slide classifications */
  sections: ClassifiedSection[];

  /** Document-level domain overlay */
  dominantDomain: DomainOverlay;

  /** Has any pricing content */
  containsPricing: boolean;

  /** Overall classification summary */
  labelDistribution: Record<PrimaryLabel, number>;
}

export interface ClassifiedSection {
  /** Page/slide number (1-indexed) */
  index: number;

  /** Raw extracted text */
  text: string;

  /** Heading or title if detected */
  heading?: string;

  /** Classification result */
  classification: ClassificationResult;

  /** Extracted requirements (if this section contains them) */
  requirements?: ExtractedRequirement[];
}

// ---------------------------------------------------------------------------
// Requirement extraction types
// ---------------------------------------------------------------------------

export interface ExtractedRequirement {
  /** Requirement ID from the source document (e.g., "3.2.1", "Q-47") */
  sourceId: string;

  /** Requirement text */
  text: string;

  /** Which backend section should address this */
  targetSection: BackendSection;

  /** Priority based on evaluation criteria if available */
  priority: "must_have" | "should_have" | "nice_to_have" | "unknown";

  /** Status in the proposal lifecycle */
  status: RequirementStatus;
}

export type RequirementStatus =
  | "parsed"
  | "mapped"
  | "draft_started"
  | "draft_complete"
  | "under_review"
  | "approved"
  | "needs_revision";

// ---------------------------------------------------------------------------
// Project-level types (proposal engagement state)
// ---------------------------------------------------------------------------

export interface ProposalProject {
  id: string;
  name: string;
  clientPersona: string;
  createdAt: string;
  updatedAt: string;

  /** All uploaded documents */
  documents: ClassifiedDocument[];

  /** All extracted requirements */
  requirements: ExtractedRequirement[];

  /** Section generation status */
  sections: ProposalSection[];

  /** Project-wide assumptions needing confirmation */
  assumptions: Assumption[];
}

export interface ProposalSection {
  /** Which backend section */
  sectionType: BackendSection;

  /** Display title */
  title: string;

  /** Requirements mapped to this section */
  requirementIds: string[];

  /** Current draft content (markdown) */
  draftContent: string;

  /** Generation status */
  status: RequirementStatus;

  /** Word/page target if specified */
  wordTarget?: number;

  /** Review notes */
  reviewNotes: string[];
}

export interface Assumption {
  id: string;
  text: string;
  impact: string;
  defaultIfUnconfirmed: string;
  status: "pending" | "confirmed" | "corrected" | "rejected";
  correctedValue?: string;
}
