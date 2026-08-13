import { Calculator, Database, ExternalLink, FileText, ShieldCheck } from "lucide-react";

import type { Evidence } from "../api/types";

interface EvidencePanelProps {
  evidence: Evidence[];
  selectedId: string | null;
  onSelect: (id: string) => void;
}

const evidenceIcons = {
  document: FileText,
  sql: Database,
  calculation: Calculator,
};

export function EvidencePanel({ evidence, selectedId, onSelect }: EvidencePanelProps) {
  const orderedEvidence = [...evidence].sort(
    (left, right) => ["document", "calculation", "sql"].indexOf(left.kind)
      - ["document", "calculation", "sql"].indexOf(right.kind),
  );
  return (
    <section className="evidence-panel" aria-labelledby="evidence-heading">
      <div className="inspector-header">
        <div>
          <p className="eyebrow">Grounding</p>
          <h2 id="evidence-heading">Evidence</h2>
        </div>
        <span>{evidence.length} {evidence.length === 1 ? "source" : "sources"}</span>
      </div>
      {evidence.length === 0 ? (
        <div className="empty-evidence">
          <ShieldCheck aria-hidden="true" size={22} />
          Evidence appears here after a supported run.
        </div>
      ) : (
        <div className="evidence-list">
          {orderedEvidence.map((item, index) => {
            const Icon = evidenceIcons[item.kind];
            const selected = (selectedId ?? orderedEvidence[0]?.id) === item.id;
            return (
              <article
                className={`evidence-item ${selected ? "evidence-item-selected" : ""}`}
                key={item.id}
              >
                <button type="button" className="evidence-select" onClick={() => onSelect(item.id)}>
                  <span className="evidence-index">E{index + 1}</span>
                  <Icon aria-hidden="true" size={16} />
                  <span>{item.kind === "document" ? "Policy document" : item.kind}</span>
                  {item.score !== null ? (
                    <span className="confidence">{Math.round(item.score * 100)}%</span>
                  ) : null}
                </button>
                <div className="evidence-content">
                  <h3>{item.title ?? item.id}</h3>
                  {item.section ? <p className="evidence-section">{item.section}</p> : null}
                  <blockquote>{item.text}</blockquote>
                  <div className="evidence-meta">
                    <code title={item.id}>{item.id.slice(0, 20)}…</code>
                    {item.source_uri ? (
                      <a href={item.source_uri} target="_blank" rel="noreferrer" aria-label="Open evidence source">
                        <ExternalLink aria-hidden="true" size={15} />
                      </a>
                    ) : null}
                  </div>
                </div>
              </article>
            );
          })}
        </div>
      )}
    </section>
  );
}
