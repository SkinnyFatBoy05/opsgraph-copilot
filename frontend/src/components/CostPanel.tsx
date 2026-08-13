import type { RunTrace } from "../api/types";

export function CostPanel({ trace }: { trace: RunTrace | null }) {
  if (!trace) return <p className="empty-panel">Runtime details appear after a run.</p>;
  const elapsed = trace.completed_at
    ? new Date(trace.completed_at).getTime() - new Date(trace.started_at).getTime()
    : 0;
  return (
    <dl className="cost-panel">
      <div><dt>Provider</dt><dd>{trace.provider}</dd></div>
      <div><dt>Model</dt><dd>{trace.model}</dd></div>
      <div><dt>Latency</dt><dd>{elapsed}ms</dd></div>
      <div><dt>Tool calls</dt><dd>{trace.tool_call_count} / 6</dd></div>
      <div><dt>Estimated cost</dt><dd>${trace.estimated_cost_usd.toFixed(6)}</dd></div>
      <div><dt>Run ID</dt><dd title={trace.run_id}>{trace.run_id.slice(0, 16)}…</dd></div>
    </dl>
  );
}
