import { BACKEND_SECTIONS } from "@/lib/classification";
import { PRIMARY_LABELS } from "@/lib/classification";

export default function Home() {
  const sections = Object.values(BACKEND_SECTIONS).sort(
    (a, b) => a.number - b.number,
  );

  const labels = Object.values(PRIMARY_LABELS).sort(
    (a, b) => b.corpusFrequency - a.corpusFrequency,
  );

  return (
    <div className="space-y-12">
      <section>
        <h2 className="text-2xl font-bold mb-2">Proposal Projects</h2>
        <p className="text-gray-400 mb-6">
          Upload RFP documents, classify content, generate proposal sections.
        </p>
        <a
          href="/intake"
          className="inline-block px-4 py-2 bg-blue-600 hover:bg-blue-500 rounded text-sm font-medium"
        >
          New Project — Upload Documents
        </a>
      </section>

      <section>
        <h3 className="text-lg font-semibold mb-4">
          Proposal Structure (9 Sections)
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {sections.map((s) => (
            <div
              key={s.id}
              className="border border-gray-800 rounded-lg p-4 hover:border-gray-600"
            >
              <div className="text-sm text-gray-500 mb-1">
                Section {s.number}
              </div>
              <div className="font-medium mb-2">{s.displayName}</div>
              <ul className="text-xs text-gray-400 space-y-1">
                {s.styleGuideNotes.map((note, i) => (
                  <li key={i}>• {note}</li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </section>

      <section>
        <h3 className="text-lg font-semibold mb-4">
          Classification Taxonomy (from 1,000-slide corpus)
        </h3>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-800 text-left text-gray-400">
                <th className="pb-2 pr-4">Label</th>
                <th className="pb-2 pr-4">Corpus %</th>
                <th className="pb-2 pr-4">Count Range</th>
                <th className="pb-2">Description</th>
              </tr>
            </thead>
            <tbody>
              {labels.map((l) => (
                <tr key={l.id} className="border-b border-gray-800/50">
                  <td className="py-2 pr-4 font-medium">{l.displayName}</td>
                  <td className="py-2 pr-4 text-gray-400">
                    {(l.corpusFrequency * 100).toFixed(1)}%
                  </td>
                  <td className="py-2 pr-4 text-gray-400">
                    {l.corpusCount[0]}–{l.corpusCount[1]}
                  </td>
                  <td className="py-2 text-gray-500 max-w-md truncate">
                    {l.description}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
