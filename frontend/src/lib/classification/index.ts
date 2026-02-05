/**
 * Classification Module
 * =====================
 * Public API for the document classification system.
 */

// Types
export type {
  PrimaryLabel,
  IntentGroup,
  DomainOverlay,
  PricingFlag,
  ConfidenceLevel,
  BackendSection,
  ClassificationResult,
  ClassifiedDocument,
  ClassifiedSection,
  DocumentType,
  DocumentMetadata,
  FileFormat,
  ExtractedRequirement,
  RequirementStatus,
  ProposalProject,
  ProposalSection,
  Assumption,
} from "./types";

// Taxonomy data
export {
  PRIMARY_LABELS,
  INTENT_GROUPS,
  DOMAIN_OVERLAYS,
  getIntentGroup,
} from "./taxonomy";

// Mapping data
export {
  LABEL_TO_SECTIONS,
  INTENT_TO_SECTIONS,
  BACKEND_SECTIONS,
  resolveBackendSections,
  refineToSingleSection,
} from "./mapping";

// Classifier functions
export {
  classifySection,
  classifyDocument,
} from "./classifier";
export type {
  ClassifyDocumentInput,
  ClassifyDocumentOutput,
} from "./classifier";
