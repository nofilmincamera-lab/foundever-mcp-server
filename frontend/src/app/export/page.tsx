"use client";

import { useState } from "react";

/**
 * PPTX Export Page
 * ================
 * Assembles a proposal deck from the slide library and generated content.
 *
 * Workflow:
 *   1. Index slide library (point to theme-organized directory)
 *   2. Browse themes and search slides
 *   3. Create a new deck (blank or from template)
 *   4. Add section slides with generated content
 *   5. Clone reference slides from the library
 *   6. Save the assembled deck
 */

// Slide library stats shape
interface LibraryStats {
  total_slides: number;
  total_themes: number;
  themes: Record<string, { slides: number }>;
}

type DeckStatus = "idle" | "created" | "building" | "saved";

const BACKEND_SECTIONS = [
  { id: "executive_summary", name: "Executive Summary", number: 1 },
  { id: "client_understanding", name: "Understanding Client Needs", number: 2 },
  { id: "solution_overview", name: "Solution Overview", number: 3 },
  { id: "delivery_model", name: "Delivery Model", number: 4 },
  { id: "technology", name: "Technology & Innovation", number: 5 },
  { id: "governance_compliance", name: "Governance & Compliance", number: 6 },
  { id: "implementation", name: "Implementation & Transition", number: 7 },
  { id: "team_leadership", name: "Team & Leadership", number: 8 },
  { id: "proof_points", name: "Proof Points & Evidence", number: 9 },
] as const;

export default function ExportPage() {
  // Library state
  const [libraryPath, setLibraryPath] = useState("");
  const [libraryStats, setLibraryStats] = useState<LibraryStats | null>(null);
  const [libraryLoading, setLibraryLoading] = useState(false);
  const [libraryError, setLibraryError] = useState("");

  // Search state
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState("");
  const [searchLoading, setSearchLoading] = useState(false);

  // Deck state
  const [deckStatus, setDeckStatus] = useState<DeckStatus>("idle");
  const [deckTitle, setDeckTitle] = useState("");
  const [deckSubtitle, setDeckSubtitle] = useState("");
  const [templatePath, setTemplatePath] = useState("");
  const [deckLog, setDeckLog] = useState<string[]>([]);
  const [outputPath, setOutputPath] = useState("output/proposal.pptx");

  // Slide addition state
  const [slideSection, setSlideSection] = useState("executive_summary");
  const [slideTitle, setSlideTitleState] = useState("");
  const [slideBody, setSlideBody] = useState("");
  const [slideNotes, setSlideNotes] = useState("");

  const appendLog = (msg: string) =>
    setDeckLog((prev) => [...prev, `[${new Date().toLocaleTimeString()}] ${msg}`]);

  // -- Library handlers --

  async function handleIndexLibrary() {
    if (!libraryPath.trim()) return;
    setLibraryLoading(true);
    setLibraryError("");
    try {
      const res = await fetch("/api/mcp/index_slide_library", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ library_path: libraryPath }),
      });
      const text = await res.text();
      if (!res.ok) throw new Error(text);
      setLibraryStats(JSON.parse(text));
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : String(e);
      setLibraryError(msg);
    } finally {
      setLibraryLoading(false);
    }
  }

  async function handleSearch() {
    if (!searchQuery.trim()) return;
    setSearchLoading(true);
    try {
      const res = await fetch("/api/mcp/search_slide_library", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: searchQuery, limit: 10 }),
      });
      setSearchResults(await res.text());
    } catch {
      setSearchResults("Search failed.");
    } finally {
      setSearchLoading(false);
    }
  }

  // -- Deck handlers --

  async function handleCreateDeck() {
    try {
      const args: Record<string, string> = {};
      if (templatePath.trim()) args.template_path = templatePath;
      if (deckTitle.trim()) args.title = deckTitle;
      if (deckSubtitle.trim()) args.subtitle = deckSubtitle;

      const res = await fetch("/api/mcp/create_proposal_deck", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(args),
      });
      const text = await res.text();
      appendLog(text);
      setDeckStatus("created");
    } catch {
      appendLog("Failed to create deck.");
    }
  }

  async function handleAddSlide() {
    if (!slideTitle.trim() || !slideBody.trim()) return;
    try {
      const res = await fetch("/api/mcp/add_proposal_slide", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          section_type: slideSection,
          title: slideTitle,
          body: slideBody,
          speaker_notes: slideNotes || undefined,
          add_divider: true,
        }),
      });
      const text = await res.text();
      appendLog(text);
      setDeckStatus("building");
      // Clear form
      setSlideTitleState("");
      setSlideBody("");
      setSlideNotes("");
    } catch {
      appendLog("Failed to add slide.");
    }
  }

  async function handleSaveDeck() {
    try {
      const res = await fetch("/api/mcp/save_proposal_deck", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ output_path: outputPath }),
      });
      const text = await res.text();
      appendLog(text);
      setDeckStatus("saved");
    } catch {
      appendLog("Failed to save deck.");
    }
  }

  return (
    <div className="space-y-10">
      <div>
        <h2 className="text-2xl font-bold font-fe-primary">PPTX Export</h2>
        <p className="text-fe-light-grey/60 mt-1">
          Assemble a proposal deck from the slide library and generated content.
        </p>
      </div>

      {/* ── Slide Library ─────────────────────────────────────────── */}
      <section className="border border-fe-indigo/15 rounded-lg p-6 space-y-4">
        <h3 className="text-lg font-bold font-fe-primary">Slide Library</h3>

        <div className="flex gap-3">
          <input
            type="text"
            placeholder="/path/to/Slide Library"
            value={libraryPath}
            onChange={(e) => setLibraryPath(e.target.value)}
            className="flex-1 bg-fe-midnight border border-fe-indigo/20 rounded px-3 py-2 text-sm text-white placeholder:text-fe-light-grey/30 focus:outline-none focus:border-fe-indigo/50"
          />
          <button
            onClick={handleIndexLibrary}
            disabled={libraryLoading}
            className="px-4 py-2 bg-fe-indigo hover:bg-fe-indigo/80 rounded text-sm font-medium transition-colors disabled:opacity-50"
          >
            {libraryLoading ? "Indexing..." : "Index Library"}
          </button>
        </div>

        {libraryError && (
          <div className="text-sm text-fe-coral bg-fe-coral/10 rounded px-3 py-2">
            {libraryError}
          </div>
        )}

        {libraryStats && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
            <div className="border border-fe-indigo/15 rounded p-3 text-center">
              <div className="text-2xl font-bold text-fe-mint">{libraryStats.total_slides}</div>
              <div className="text-fe-light-grey/50">Slides</div>
            </div>
            <div className="border border-fe-indigo/15 rounded p-3 text-center">
              <div className="text-2xl font-bold text-fe-mint">{libraryStats.total_themes}</div>
              <div className="text-fe-light-grey/50">Themes</div>
            </div>
            {Object.entries(libraryStats.themes)
              .sort(([, a], [, b]) => b.slides - a.slides)
              .slice(0, 6)
              .map(([name, info]) => (
                <div key={name} className="border border-fe-indigo/15 rounded p-3">
                  <div className="font-medium text-fe-light-grey/80 truncate">{name}</div>
                  <div className="text-fe-indigo/70 text-xs">{info.slides} slides</div>
                </div>
              ))}
          </div>
        )}

        {/* Search */}
        {libraryStats && (
          <div className="space-y-3 pt-2">
            <div className="flex gap-3">
              <input
                type="text"
                placeholder="Search slides (e.g., fraud detection, staffing model)"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleSearch()}
                className="flex-1 bg-fe-midnight border border-fe-indigo/20 rounded px-3 py-2 text-sm text-white placeholder:text-fe-light-grey/30 focus:outline-none focus:border-fe-indigo/50"
              />
              <button
                onClick={handleSearch}
                disabled={searchLoading}
                className="px-4 py-2 bg-fe-indigo/20 hover:bg-fe-indigo/30 border border-fe-indigo/30 rounded text-sm transition-colors disabled:opacity-50"
              >
                {searchLoading ? "Searching..." : "Search"}
              </button>
            </div>
            {searchResults && (
              <pre className="text-xs text-fe-light-grey/60 bg-fe-midnight/80 border border-fe-indigo/10 rounded p-3 max-h-64 overflow-y-auto whitespace-pre-wrap">
                {searchResults}
              </pre>
            )}
          </div>
        )}
      </section>

      {/* ── Deck Builder ──────────────────────────────────────────── */}
      <section className="border border-fe-indigo/15 rounded-lg p-6 space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-bold font-fe-primary">Deck Builder</h3>
          <span className="text-xs text-fe-indigo/60 uppercase tracking-wider">
            {deckStatus === "idle" && "No deck"}
            {deckStatus === "created" && "Deck created"}
            {deckStatus === "building" && "Building..."}
            {deckStatus === "saved" && "Saved"}
          </span>
        </div>

        {/* Create deck */}
        {deckStatus === "idle" && (
          <div className="space-y-3">
            <input
              type="text"
              placeholder="Template path (optional)"
              value={templatePath}
              onChange={(e) => setTemplatePath(e.target.value)}
              className="w-full bg-fe-midnight border border-fe-indigo/20 rounded px-3 py-2 text-sm text-white placeholder:text-fe-light-grey/30 focus:outline-none focus:border-fe-indigo/50"
            />
            <div className="grid grid-cols-2 gap-3">
              <input
                type="text"
                placeholder="Proposal Title"
                value={deckTitle}
                onChange={(e) => setDeckTitle(e.target.value)}
                className="bg-fe-midnight border border-fe-indigo/20 rounded px-3 py-2 text-sm text-white placeholder:text-fe-light-grey/30 focus:outline-none focus:border-fe-indigo/50"
              />
              <input
                type="text"
                placeholder="Subtitle (optional)"
                value={deckSubtitle}
                onChange={(e) => setDeckSubtitle(e.target.value)}
                className="bg-fe-midnight border border-fe-indigo/20 rounded px-3 py-2 text-sm text-white placeholder:text-fe-light-grey/30 focus:outline-none focus:border-fe-indigo/50"
              />
            </div>
            <button
              onClick={handleCreateDeck}
              className="px-4 py-2 bg-fe-indigo hover:bg-fe-indigo/80 rounded text-sm font-medium transition-colors"
            >
              Create Deck
            </button>
          </div>
        )}

        {/* Add slides */}
        {(deckStatus === "created" || deckStatus === "building") && (
          <div className="space-y-3">
            <div className="grid grid-cols-2 gap-3">
              <select
                value={slideSection}
                onChange={(e) => setSlideSection(e.target.value)}
                className="bg-fe-midnight border border-fe-indigo/20 rounded px-3 py-2 text-sm text-white focus:outline-none focus:border-fe-indigo/50"
              >
                {BACKEND_SECTIONS.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.number}. {s.name}
                  </option>
                ))}
              </select>
              <input
                type="text"
                placeholder="Slide title"
                value={slideTitle}
                onChange={(e) => setSlideTitleState(e.target.value)}
                className="bg-fe-midnight border border-fe-indigo/20 rounded px-3 py-2 text-sm text-white placeholder:text-fe-light-grey/30 focus:outline-none focus:border-fe-indigo/50"
              />
            </div>
            <textarea
              placeholder="Slide body (supports <b>, <i>, <u>, <br> tags)"
              value={slideBody}
              onChange={(e) => setSlideBody(e.target.value)}
              rows={4}
              className="w-full bg-fe-midnight border border-fe-indigo/20 rounded px-3 py-2 text-sm text-white placeholder:text-fe-light-grey/30 focus:outline-none focus:border-fe-indigo/50 resize-y"
            />
            <textarea
              placeholder="Speaker notes — evidence IDs, sources (optional)"
              value={slideNotes}
              onChange={(e) => setSlideNotes(e.target.value)}
              rows={2}
              className="w-full bg-fe-midnight border border-fe-indigo/20 rounded px-3 py-2 text-sm text-fe-light-grey/60 placeholder:text-fe-light-grey/30 focus:outline-none focus:border-fe-indigo/50 resize-y"
            />
            <div className="flex gap-3">
              <button
                onClick={handleAddSlide}
                className="px-4 py-2 bg-fe-indigo hover:bg-fe-indigo/80 rounded text-sm font-medium transition-colors"
              >
                Add Slide
              </button>
              <div className="flex-1" />
              <input
                type="text"
                placeholder="output/proposal.pptx"
                value={outputPath}
                onChange={(e) => setOutputPath(e.target.value)}
                className="w-64 bg-fe-midnight border border-fe-indigo/20 rounded px-3 py-2 text-sm text-white placeholder:text-fe-light-grey/30 focus:outline-none focus:border-fe-indigo/50"
              />
              <button
                onClick={handleSaveDeck}
                className="px-4 py-2 bg-fe-mint/20 hover:bg-fe-mint/30 text-fe-mint border border-fe-mint/30 rounded text-sm font-medium transition-colors"
              >
                Save Deck
              </button>
            </div>
          </div>
        )}

        {/* Saved confirmation */}
        {deckStatus === "saved" && (
          <div className="space-y-3">
            <div className="text-sm text-fe-mint bg-fe-mint/10 rounded px-3 py-2">
              Deck saved to {outputPath}
            </div>
            <button
              onClick={() => {
                setDeckStatus("idle");
                setDeckLog([]);
              }}
              className="px-4 py-2 bg-fe-indigo/20 hover:bg-fe-indigo/30 border border-fe-indigo/30 rounded text-sm transition-colors"
            >
              Start New Deck
            </button>
          </div>
        )}

        {/* Build log */}
        {deckLog.length > 0 && (
          <pre className="text-xs text-fe-light-grey/50 bg-fe-midnight/80 border border-fe-indigo/10 rounded p-3 max-h-48 overflow-y-auto whitespace-pre-wrap">
            {deckLog.join("\n")}
          </pre>
        )}
      </section>

      {/* ── Section Reference ─────────────────────────────────────── */}
      <section className="border border-fe-indigo/15 rounded-lg p-6">
        <h3 className="text-lg font-bold mb-4 font-fe-primary">
          Proposal Sections (9-Section Structure)
        </h3>
        <div className="grid grid-cols-3 gap-3 text-sm">
          {BACKEND_SECTIONS.map((s) => (
            <div
              key={s.id}
              className="border border-fe-indigo/10 rounded p-3 hover:border-fe-indigo/30 transition-colors"
            >
              <div className="text-fe-indigo/60 text-xs">Section {s.number}</div>
              <div className="font-medium text-fe-light-grey/80">{s.name}</div>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
