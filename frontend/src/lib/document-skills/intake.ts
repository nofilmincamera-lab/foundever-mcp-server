/**
 * Document Intake Pipeline
 * ========================
 * Handles the full document intake flow:
 *   1. Upload → extract text (calls MCP server's document tools)
 *   2. Classify each page/slide (uses FE keyword classifier)
 *   3. Detect document type
 *   4. Extract requirements (for RFP/RFI documents)
 *   5. Map requirements to backend sections
 *
 * This is the orchestration layer between the MCP server's document
 * parsing tools and the FE classification model.
 */

import type {
  FileFormat,
  ClassifiedDocument,
  ClassifiedSection,
  ExtractedRequirement,
  BackendSection,
} from "../classification/types";
import { classifyDocument } from "../classification/classifier";
import { refineToSingleSection } from "../classification/mapping";
import type { MCPClient } from "../mcp/client";

// ---------------------------------------------------------------------------
// Document intake
// ---------------------------------------------------------------------------

export interface IntakeResult {
  document: ClassifiedDocument;
  requirements: ExtractedRequirement[];
  warnings: string[];
}

/**
 * Process a single uploaded document through the full intake pipeline.
 */
export async function processDocument(
  mcp: MCPClient,
  filePath: string,
  fileName: string,
): Promise<IntakeResult> {
  const warnings: string[] = [];

  // 1. Detect format
  const format = detectFormat(fileName);
  if (!format) {
    throw new Error(`Unsupported file format: ${fileName}`);
  }

  // 2. Extract text via MCP server
  const pages = await extractPages(mcp, filePath, format);
  if (pages.length === 0) {
    warnings.push("No text content extracted from document.");
  }

  // 3. Classify
  const classified = classifyDocument({
    fileName,
    fileFormat: format,
    pages,
  });

  // 4. Extract requirements from RFP/RFI documents
  let requirements: ExtractedRequirement[] = [];
  if (classified.documentType === "rfp" || classified.documentType === "rfi") {
    requirements = extractRequirements(classified.sections);
  }

  // 5. Build classified document
  const document: ClassifiedDocument = {
    id: crypto.randomUUID(),
    fileName,
    fileFormat: format,
    documentType: classified.documentType,
    uploadedAt: new Date().toISOString(),
    pageCount: pages.length,
    slideCount: format === "pptx" ? pages.length : undefined,
    sections: classified.sections,
    dominantDomain: classified.dominantDomain,
    containsPricing: classified.containsPricing,
    labelDistribution: classified.labelDistribution,
  };

  // 6. Pricing warning
  if (classified.containsPricing) {
    warnings.push(
      "Document contains pricing content. Per style guide, pricing is excluded from proposal body. Flagged for commercial appendix.",
    );
  }

  return { document, requirements, warnings };
}

// ---------------------------------------------------------------------------
// Text extraction via MCP server document tools
// ---------------------------------------------------------------------------

/**
 * Extract pages/slides as an array of text strings.
 * Calls the appropriate MCP document tool based on format.
 */
async function extractPages(
  mcp: MCPClient,
  filePath: string,
  format: FileFormat,
): Promise<string[]> {
  let rawText: string;

  switch (format) {
    case "pdf":
      rawText = await mcp.callTool("pdf_extract_text", {
        file_path: filePath,
        layout: true,
      });
      return splitByPageMarkers(rawText, /---\s*PAGE\s+\d+\s*---/i);

    case "docx":
      rawText = await mcp.callTool("docx_extract_text", {
        file_path: filePath,
      });
      // DOCX doesn't have page markers in extracted text — treat as sections
      return splitBySections(rawText);

    case "xlsx":
      rawText = await mcp.callTool("xlsx_read", {
        file_path: filePath,
      });
      // Excel returns JSON — each sheet becomes a "page"
      return splitExcelSheets(rawText);

    case "pptx":
      rawText = await mcp.callTool("pptx_extract_text", {
        file_path: filePath,
      });
      return splitByPageMarkers(rawText, /---\s*SLIDE\s+\d+\s*---/i);

    default:
      return [rawText!];
  }
}

// ---------------------------------------------------------------------------
// Requirement extraction
// ---------------------------------------------------------------------------

/**
 * Extract individual requirements from classified sections.
 * Looks for numbered patterns, question formats, and table rows.
 */
function extractRequirements(
  sections: ClassifiedSection[],
): ExtractedRequirement[] {
  const requirements: ExtractedRequirement[] = [];
  let reqCounter = 0;

  for (const section of sections) {
    const text = section.text;
    const lines = text.split("\n");

    for (const line of lines) {
      const trimmed = line.trim();
      if (!trimmed) continue;

      // Pattern 1: Numbered requirements (3.2.1, 4.1, etc.)
      const numberedMatch = trimmed.match(
        /^(\d+(?:\.\d+)*)\s*[.):]\s*(.+)/,
      );
      if (numberedMatch) {
        reqCounter++;
        const targetSection = refineToSingleSection(
          section.classification.primaryLabel,
          numberedMatch[2],
        );
        requirements.push({
          sourceId: numberedMatch[1],
          text: numberedMatch[2].trim(),
          targetSection,
          priority: "unknown",
          status: "parsed",
        });
        continue;
      }

      // Pattern 2: Lettered requirements (a), b), A., B.)
      const letteredMatch = trimmed.match(
        /^[a-zA-Z]\s*[.)]\s*(.{20,})/,
      );
      if (letteredMatch) {
        reqCounter++;
        const targetSection = refineToSingleSection(
          section.classification.primaryLabel,
          letteredMatch[1],
        );
        requirements.push({
          sourceId: `Q-${reqCounter}`,
          text: letteredMatch[1].trim(),
          targetSection,
          priority: "unknown",
          status: "parsed",
        });
        continue;
      }

      // Pattern 3: Question format
      const questionMatch = trimmed.match(
        /^(?:Q\d*[.:])?\s*((?:Please |Describe |Provide |Explain |How |What |Where |When ).{20,})/i,
      );
      if (questionMatch) {
        reqCounter++;
        const targetSection = refineToSingleSection(
          section.classification.primaryLabel,
          questionMatch[1],
        );
        requirements.push({
          sourceId: `Q-${reqCounter}`,
          text: questionMatch[1].trim(),
          targetSection,
          priority: "unknown",
          status: "parsed",
        });
      }
    }
  }

  return requirements;
}

// ---------------------------------------------------------------------------
// Text splitting helpers
// ---------------------------------------------------------------------------

function splitByPageMarkers(text: string, pattern: RegExp): string[] {
  const parts = text.split(pattern).filter((p) => p.trim().length > 0);
  return parts.length > 0 ? parts : [text];
}

function splitBySections(text: string): string[] {
  // Split on heading-like patterns (lines that look like section headers)
  const lines = text.split("\n");
  const sections: string[] = [];
  let current: string[] = [];

  for (const line of lines) {
    // Detect section breaks: all-caps lines, numbered headers, etc.
    const isHeader =
      /^#{1,4}\s/.test(line) ||
      /^[A-Z][A-Z\s]{5,}$/.test(line.trim()) ||
      /^\d+\.\s+[A-Z]/.test(line.trim());

    if (isHeader && current.length > 0) {
      sections.push(current.join("\n"));
      current = [];
    }
    current.push(line);
  }

  if (current.length > 0) {
    sections.push(current.join("\n"));
  }

  return sections.length > 0 ? sections : [text];
}

function splitExcelSheets(jsonText: string): string[] {
  try {
    const data = JSON.parse(jsonText);
    if (typeof data === "object" && !Array.isArray(data)) {
      // Multi-sheet: { "Sheet1": [...], "Sheet2": [...] }
      return Object.entries(data).map(
        ([name, rows]) =>
          `Sheet: ${name}\n${JSON.stringify(rows, null, 2)}`,
      );
    }
    // Single array of records
    return [jsonText];
  } catch {
    return [jsonText];
  }
}

// ---------------------------------------------------------------------------
// Format detection
// ---------------------------------------------------------------------------

function detectFormat(fileName: string): FileFormat | null {
  const ext = fileName.toLowerCase().split(".").pop();
  switch (ext) {
    case "pdf":
      return "pdf";
    case "docx":
    case "doc":
      return "docx";
    case "xlsx":
    case "xls":
      return "xlsx";
    case "pptx":
    case "ppt":
      return "pptx";
    default:
      return null;
  }
}
