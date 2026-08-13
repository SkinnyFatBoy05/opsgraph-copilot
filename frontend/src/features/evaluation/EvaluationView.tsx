import { AlertTriangle, BadgeCheck, Gauge, ShieldCheck } from "lucide-react";
import { useEffect, useState } from "react";

import { apiClient } from "../../api/client";
import type { EvaluationReport } from "../../api/types";

const visibleMetrics = [
  ["route_accuracy", "Route accuracy"],
  ["citation_validity", "Citation validity"],
  ["sql_safety", "SQL safety"],
  ["numeric_preservation", "Numeric preservation"],
] as const;

function percentage(value: number | undefined): string {
  return `${((value ?? 0) * 100).toFixed(0)}%`;
}

function readableFailure(value: string): string {
  return value.replaceAll("_", " ");
}

export function EvaluationView() {
  const [report, setReport] = useState<EvaluationReport | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    apiClient
      .latestEvaluation(controller.signal)
      .then(setReport)
      .catch((reason: unknown) => {
        if (!controller.signal.aborted) {
          setError(reason instanceof Error ? reason.message : "Evaluation report unavailable");
        }
      });
    return () => controller.abort();
  }, []);

  return (
    <main className="evaluation-workspace">
      <header className="evaluation-heading">
        <p className="eyebrow">Release evidence</p>
        <h1>Evaluations</h1>
        <p>Deterministic quality and safety checks for the guarded agent workflow.</p>
      </header>

      {error ? <p className="evaluation-error" role="alert">{error}</p> : null}
      {!report && !error ? <p className="evaluation-loading" role="status">Loading verified report…</p> : null}

      {report ? (
        <div className="evaluation-content">
          <section className="evaluation-summary" aria-label="Evaluation summary">
            <div>
              <BadgeCheck aria-hidden="true" />
              <span>Cases passed</span>
              <strong>{report.passed_cases} / {report.total_cases}</strong>
            </div>
            <div>
              <Gauge aria-hidden="true" />
              <span>Mean latency</span>
              <strong>{(report.metrics.mean_latency_ms ?? 0).toFixed(1)} ms</strong>
            </div>
            <div>
              <ShieldCheck aria-hidden="true" />
              <span>Estimated model cost</span>
              <strong>${report.estimated_cost_usd}</strong>
            </div>
          </section>

          <section className="metric-grid" aria-labelledby="metric-heading">
            <h2 id="metric-heading">Quality metrics</h2>
            {visibleMetrics.map(([key, label]) => (
              <article key={key} className="metric-card">
                <span>{label}</span>
                <strong>{percentage(report.metrics[key])}</strong>
                <div className="metric-track" aria-hidden="true">
                  <span style={{ width: percentage(report.metrics[key]) }} />
                </div>
              </article>
            ))}
          </section>

          <section
            className={`release-gate ${report.release_failures.length ? "release-gate-failed" : ""}`}
            aria-labelledby="release-gate-heading"
          >
            <div>
              {report.release_failures.length ? <AlertTriangle aria-hidden="true" /> : <ShieldCheck aria-hidden="true" />}
              <div>
                <h2 id="release-gate-heading">Release gate</h2>
                {report.release_failures.length ? (
                  <ul>
                    {report.release_failures.map((failure) => (
                      <li key={failure}>{readableFailure(failure)}</li>
                    ))}
                  </ul>
                ) : (
                  <p>No release-blocking failures detected.</p>
                )}
              </div>
            </div>
          </section>

          <footer className="evaluation-provenance">
            <span>{report.deterministic ? "Deterministic fake provider" : report.provider}</span>
            <span>Suite {report.suite_version}</span>
            <span>Generated {new Date(report.generated_at).toLocaleString()}</span>
          </footer>
        </div>
      ) : null}
    </main>
  );
}
