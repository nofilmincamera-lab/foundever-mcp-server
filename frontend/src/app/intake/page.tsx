"use client";

import { useState } from "react";
import type { ClassifiedDocument, ExtractedRequirement } from "@/lib/classification";

interface IntakeState {
  status: "idle" | "uploading" | "classifying" | "done" | "error";
  documents: ClassifiedDocument[];
  requirements: ExtractedRequirement[];
  warnings: string[];
  error?: string;
}

export default function IntakePage() {
  const [state, setState] = useState<IntakeState>({
    status: "idle",
    documents: [],
    requirements: [],
    warnings: [],
  });

  async function handleUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const files = e.target.files;
    if (!files || files.length === 0) return;

    setState((s) => ({ ...s, status: "uploading" }));

    // TODO: Implement file upload to API route that calls MCP server
    // For now, show the upload flow structure
    setState((s) => ({
      ...s,
      status: "done",
      warnings: [
        `${files.length} file(s) selected. Connect to MCP server to process.`,
      ],
    }));
  }

  return (
    <div className="space-y-8">
      <div>
        <h2 className="text-2xl font-bold mb-2">Document Intake</h2>
        <p className="text-fe-light-grey/60">
          Upload RFP/RFI documents. The system will classify content, extract
          requirements, and map them to proposal sections.
        </p>
      </div>

      {/* Upload zone */}
      <div className="border-2 border-dashed border-fe-indigo/20 rounded-xl p-12 text-center hover:border-fe-indigo/40 transition-colors">
        <input
          type="file"
          multiple
          accept=".pdf,.docx,.doc,.xlsx,.xls,.pptx,.ppt"
          onChange={handleUpload}
          className="hidden"
          id="file-upload"
        />
        <label
          htmlFor="file-upload"
          className="cursor-pointer space-y-3 block"
        >
          <div className="text-4xl">+</div>
          <div className="text-lg font-medium">Drop documents here</div>
          <div className="text-sm text-fe-light-grey/50">
            PDF, DOCX, XLSX, PPTX — RFPs, addenda, past proposals, score sheets
          </div>
        </label>
      </div>

      {/* Status */}
      {state.status !== "idle" && (
        <div className="space-y-4">
          <div className="flex items-center gap-2 text-sm">
            <span
              className={`inline-block w-2 h-2 rounded-full ${
                state.status === "done"
                  ? "bg-fe-mint"
                  : state.status === "error"
                    ? "bg-fe-coral"
                    : "bg-fe-lemon animate-pulse"
              }`}
            />
            <span className="text-fe-light-grey/80 capitalize">{state.status}</span>
          </div>

          {state.warnings.map((w, i) => (
            <div
              key={i}
              className="text-sm text-fe-lemon/80 bg-fe-lemon/10 rounded px-3 py-2"
            >
              {w}
            </div>
          ))}
        </div>
      )}

      {/* Classification pipeline overview */}
      <div className="border border-fe-indigo/15 rounded-lg p-6">
        <h3 className="font-semibold mb-4 font-fe-primary">Classification Pipeline</h3>
        <ol className="text-sm text-fe-light-grey/60 space-y-3">
          <li className="flex gap-3">
            <span className="text-fe-indigo/40 font-mono w-6">1.</span>
            <div>
              <span className="text-fe-light-grey/80">Extract text</span> — MCP
              server parses PDF/DOCX/XLSX/PPTX via document tools
            </div>
          </li>
          <li className="flex gap-3">
            <span className="text-fe-indigo/40 font-mono w-6">2.</span>
            <div>
              <span className="text-fe-light-grey/80">Classify pages</span> — Keyword
              classifier assigns primary label from 9-label taxonomy
            </div>
          </li>
          <li className="flex gap-3">
            <span className="text-fe-indigo/40 font-mono w-6">3.</span>
            <div>
              <span className="text-fe-light-grey/80">Detect overlays</span> — Domain,
              pricing flag, confidence level
            </div>
          </li>
          <li className="flex gap-3">
            <span className="text-fe-indigo/40 font-mono w-6">4.</span>
            <div>
              <span className="text-fe-light-grey/80">Extract requirements</span> —
              Numbered items, questions, compliance matrix rows
            </div>
          </li>
          <li className="flex gap-3">
            <span className="text-fe-indigo/40 font-mono w-6">5.</span>
            <div>
              <span className="text-fe-light-grey/80">Map to sections</span> — Route
              requirements to backend's 9-section proposal structure
            </div>
          </li>
          <li className="flex gap-3">
            <span className="text-fe-indigo/40 font-mono w-6">6.</span>
            <div>
              <span className="text-fe-light-grey/80">Refine with LLM</span> — Langbase
              pipe resolves low-confidence classifications
            </div>
          </li>
        </ol>
      </div>

      {/* Supported formats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
        {[
          { format: "PDF", desc: "RFP documents, addenda" },
          { format: "DOCX", desc: "Word proposals, requirements" },
          { format: "XLSX", desc: "Q&A matrices, score sheets" },
          { format: "PPTX", desc: "Orals decks, past presentations" },
        ].map((f) => (
          <div
            key={f.format}
            className="border border-fe-indigo/15 rounded p-3"
          >
            <div className="font-mono font-medium text-fe-light-grey/80">
              {f.format}
            </div>
            <div className="text-fe-light-grey/50 text-xs mt-1">{f.desc}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
