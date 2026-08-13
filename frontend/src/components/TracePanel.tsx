import { CheckCircle2, GitBranch } from "lucide-react";

import type { RunTrace } from "../api/types";

export function TracePanel({ trace }: { trace: RunTrace | null }) {
  if (!trace) return <p className="empty-panel">Agent steps appear after a run.</p>;
  return (
    <section className="trace-panel" aria-label="Agent trace">
      <div className="trace-route"><GitBranch aria-hidden="true" size={16} /> Route: <strong>{trace.route}</strong></div>
      <ol>
        {trace.agents.map((agent) => (
          <li key={agent}>
            <span className="trace-node"><CheckCircle2 aria-hidden="true" size={16} /></span>
            <div><strong>{agent}</strong><span>{agent.replaceAll("_", " ")}</span></div>
          </li>
        ))}
      </ol>
    </section>
  );
}
