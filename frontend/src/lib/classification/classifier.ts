/**
 * Document Classifier
 * ===================
 * Classifies document sections/slides into the 3-layer taxonomy.
 *
 * Two classification modes:
 *   1. Keyword-based (fast, no API calls — for pre-classification and routing)
 *   2. LLM-based (accurate, calls Langbase pipe — for final classification)
 *
 * The keyword classifier is designed as a first pass. It's good enough for
 * routing and UI display. The LLM classifier refines ambiguous cases.
 */

import type {
  PrimaryLabel,
  DomainOverlay,
  PricingFlag,
  ConfidenceLevel,
  ClassificationResult,
  ClassifiedSection,
  DocumentType,
  FileFormat,
} from "./types";
import { PRIMARY_LABELS, DOMAIN_OVERLAYS, getIntentGroup } from "./taxonomy";
import { resolveBackendSections } from "./mapping";

// ---------------------------------------------------------------------------
// Keyword-based classifier (Layer 2 primary label)
// ---------------------------------------------------------------------------

interface KeywordScore {
  label: PrimaryLabel;
  score: number;
  matchedKeywords: string[];
}

/**
 * Score text against all primary labels using keyword matching.
 * Returns sorted scores, highest first.
 */
function scoreByKeywords(text: string): KeywordScore[] {
  const lowerText = text.toLowerCase();
  const scores: KeywordScore[] = [];

  for (const [labelId, def] of Object.entries(PRIMARY_LABELS)) {
    const matched: string[] = [];
    for (const kw of def.signalKeywords) {
      if (lowerText.includes(kw.toLowerCase())) {
        matched.push(kw);
      }
    }

    // Score = matched keywords / total keywords, weighted by corpus frequency
    // Labels with fewer keywords need fewer matches to score high
    const keywordDensity =
      def.signalKeywords.length > 0
        ? matched.length / Math.sqrt(def.signalKeywords.length)
        : 0;

    scores.push({
      label: labelId as PrimaryLabel,
      score: keywordDensity,
      matchedKeywords: matched,
    });
  }

  return scores.sort((a, b) => b.score - a.score);
}

/**
 * Detect domain overlay from text.
 */
function detectDomain(text: string): DomainOverlay {
  const lowerText = text.toLowerCase();
  let bestDomain: DomainOverlay = "general";
  let bestScore = 0;

  for (const [domainId, def] of Object.entries(DOMAIN_OVERLAYS)) {
    if (domainId === "general") continue;
    const hits = def.signalKeywords.filter((kw) =>
      lowerText.includes(kw.toLowerCase()),
    );
    if (hits.length > bestScore) {
      bestScore = hits.length;
      bestDomain = domainId as DomainOverlay;
    }
  }

  return bestDomain;
}

/**
 * Detect pricing flag from text.
 * Pricing is orthogonal — it's a flag, not a primary label.
 */
function detectPricing(text: string): PricingFlag {
  const lowerText = text.toLowerCase();

  const strongPricingSignals = [
    "pricing", "rate card", "cost per", "hourly rate", "per fte",
    "total cost", "commercial terms", "pricing model",
  ];

  const weakPricingSignals = [
    "cost", "savings", "ROI", "budget", "investment", "commercial",
  ];

  const strongHits = strongPricingSignals.filter((s) =>
    lowerText.includes(s),
  );
  if (strongHits.length >= 1) return "has_pricing";

  const weakHits = weakPricingSignals.filter((s) => lowerText.includes(s));
  if (weakHits.length >= 2) return "pricing_adjacent";

  return "no_pricing";
}

/**
 * Determine confidence level from score.
 */
function toConfidenceLevel(score: number): ConfidenceLevel {
  if (score >= 0.6) return "high";
  if (score >= 0.3) return "medium";
  return "low";
}

// ---------------------------------------------------------------------------
// Public API: classify a single section of text
// ---------------------------------------------------------------------------

/**
 * Classify a text section using keyword matching.
 * Fast, synchronous, no API calls. Good enough for routing.
 */
export function classifySection(text: string): ClassificationResult {
  const scores = scoreByKeywords(text);
  const top = scores[0];
  const runner = scores[1];

  // If top score is 0, it's unclassified
  if (!top || top.score === 0) {
    return {
      primaryLabel: "unclassified",
      intentGroup: "structural",
      domain: detectDomain(text),
      pricingFlag: detectPricing(text),
      confidence: 0,
      confidenceLevel: "low",
      backendSections: [],
      secondaryLabels: [],
    };
  }

  // Confidence = gap between top and runner-up
  const gap = runner ? top.score - runner.score : top.score;
  const confidence = Math.min(1, gap + top.score * 0.5);

  // Secondary labels: any score > 50% of top score
  const secondaryLabels = scores
    .slice(1)
    .filter((s) => s.score > top.score * 0.5 && s.score > 0)
    .map((s) => s.label);

  return {
    primaryLabel: top.label,
    intentGroup: getIntentGroup(top.label),
    domain: detectDomain(text),
    pricingFlag: detectPricing(text),
    confidence: Math.round(confidence * 100) / 100,
    confidenceLevel: toConfidenceLevel(confidence),
    backendSections: resolveBackendSections(top.label),
    secondaryLabels,
  };
}

// ---------------------------------------------------------------------------
// Classify a full document (multiple sections/pages/slides)
// ---------------------------------------------------------------------------

export interface ClassifyDocumentInput {
  fileName: string;
  fileFormat: FileFormat;
  /** Array of page/slide text content, in order */
  pages: string[];
}

export interface ClassifyDocumentOutput {
  documentType: DocumentType;
  sections: ClassifiedSection[];
  dominantDomain: DomainOverlay;
  containsPricing: boolean;
  labelDistribution: Record<PrimaryLabel, number>;
}

/**
 * Classify an entire document's pages/slides.
 */
export function classifyDocument(
  input: ClassifyDocumentInput,
): ClassifyDocumentOutput {
  const sections: ClassifiedSection[] = input.pages.map((text, i) => ({
    index: i + 1,
    text,
    heading: extractHeading(text),
    classification: classifySection(text),
  }));

  // Aggregate label distribution
  const dist: Record<string, number> = {};
  for (const s of sections) {
    const label = s.classification.primaryLabel;
    dist[label] = (dist[label] || 0) + 1;
  }

  // Dominant domain = most common non-general domain
  const domainCounts: Record<string, number> = {};
  for (const s of sections) {
    const d = s.classification.domain;
    if (d !== "general") {
      domainCounts[d] = (domainCounts[d] || 0) + 1;
    }
  }
  const dominantDomain = (
    Object.entries(domainCounts).sort(([, a], [, b]) => b - a)[0]?.[0] ?? "general"
  ) as DomainOverlay;

  // Pricing detection
  const containsPricing = sections.some(
    (s) => s.classification.pricingFlag === "has_pricing",
  );

  // Document type inference
  const documentType = inferDocumentType(input, sections);

  return {
    documentType,
    sections,
    dominantDomain,
    containsPricing,
    labelDistribution: dist as Record<PrimaryLabel, number>,
  };
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/**
 * Extract heading from text (first non-empty line, if short enough).
 */
function extractHeading(text: string): string | undefined {
  const lines = text.split("\n").filter((l) => l.trim().length > 0);
  if (lines.length === 0) return undefined;
  const first = lines[0].trim();
  // Headings are typically short
  if (first.length <= 120) return first;
  return undefined;
}

/**
 * Infer document type from filename, format, and content signals.
 */
function inferDocumentType(
  input: ClassifyDocumentInput,
  sections: ClassifiedSection[],
): DocumentType {
  const fn = input.fileName.toLowerCase();

  // Filename-based signals
  if (fn.includes("rfp")) return "rfp";
  if (fn.includes("rfi")) return "rfi";
  if (fn.includes("oral") || fn.includes("presentation")) return "orals";
  if (fn.includes("addend")) return "addendum";
  if (fn.includes("score") || fn.includes("evaluation")) return "score_sheet";
  if (fn.includes("compliance") && fn.includes("matrix")) return "compliance_matrix";
  if (fn.includes("past") || fn.includes("previous") || fn.includes("prior")) return "past_proposal";

  // Format-based signals
  if (input.fileFormat === "pptx") return "orals";
  if (input.fileFormat === "xlsx") {
    // Excel with lots of pricing → score sheet or compliance matrix
    const hasPricing = sections.some(
      (s) => s.classification.pricingFlag === "has_pricing",
    );
    if (hasPricing) return "score_sheet";
    return "rfp"; // Excel RFP question sheets
  }

  // Content-based signals: if most sections are "other" + "executive_summary",
  // it's likely a past proposal
  const labelDist = sections.reduce(
    (acc, s) => {
      acc[s.classification.primaryLabel] =
        (acc[s.classification.primaryLabel] || 0) + 1;
      return acc;
    },
    {} as Record<string, number>,
  );

  const totalSections = sections.length;
  if (totalSections === 0) return "unknown";

  // Heavy on case studies + proof → past proposal
  const caseStudyPct = (labelDist["case_study"] || 0) / totalSections;
  if (caseStudyPct > 0.3) return "past_proposal";

  // Default for DOCX/PDF
  return "rfp";
}
