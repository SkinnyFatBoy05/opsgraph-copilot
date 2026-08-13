import { CheckCircle2, CircleHelp, LoaderCircle, TriangleAlert } from "lucide-react";

import type { ChatResponse } from "../api/types";

interface AnswerPanelProps {
  response: ChatResponse | null;
  busy: boolean;
  error: string | null;
}

function elapsedMilliseconds(response: ChatResponse): number {
  if (!response.trace.completed_at) return 0;
  return Math.max(
    0,
    new Date(response.trace.completed_at).getTime() - new Date(response.trace.started_at).getTime(),
  );
}

export function AnswerPanel({ response, busy, error }: AnswerPanelProps) {
  if (busy) {
    return (
      <div className="run-state run-state-loading" role="status" aria-live="polite">
        <LoaderCircle className="spin" aria-hidden="true" size={20} />
        Retrieving evidence and validating tools…
      </div>
    );
  }
  if (error) {
    return (
      <div className="run-state run-state-error" role="alert">
        <TriangleAlert aria-hidden="true" size={20} />
        <span>{error}</span>
      </div>
    );
  }
  if (!response) return null;

  const manualReview = response.status === "manual_review";
  const StatusIcon = manualReview ? CircleHelp : CheckCircle2;
  const elapsed = elapsedMilliseconds(response);

  return (
    <section className="answer-section" aria-labelledby="answer-heading">
      <div className={`run-state ${manualReview ? "run-state-review" : "run-state-success"}`}>
        <StatusIcon aria-hidden="true" size={20} />
        <strong>{manualReview ? "Manual review" : "Completed"}</strong>
        <span aria-hidden="true">·</span>
        <span>{elapsed < 1000 ? `${elapsed}ms` : `${(elapsed / 1000).toFixed(1)}s`}</span>
        {response.trace.cached ? <span className="status-pill">Cached</span> : null}
        {response.error_code ? <code className="error-code">{response.error_code}</code> : null}
      </div>
      <h2 id="answer-heading">Answer</h2>
      <p className="answer-copy">{response.answer}</p>
      {response.sql && response.sql.rows.length > 0 ? (
        <div className="result-block">
          <div className="result-heading">
            <h3>Operational query result</h3>
            <span>{response.sql.row_count} {response.sql.row_count === 1 ? "row" : "rows"}</span>
          </div>
          <div className="table-scroller" tabIndex={0} aria-label="Scrollable query results">
            <table>
              <thead>
                <tr>
                  {response.sql.columns.map((column) => <th key={column}>{column.replaceAll("_", " ")}</th>)}
                </tr>
              </thead>
              <tbody>
                {response.sql.rows.map((row, rowIndex) => (
                  <tr key={`${rowIndex}-${String(row[0])}`}>
                    {row.map((value, columnIndex) => (
                      <td key={`${columnIndex}-${String(value)}`}>{String(value ?? "—")}</td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      ) : null}
      <div className="limitation-line">
        {response.limitations.map((limitation) => <span key={limitation}>{limitation}</span>)}
      </div>
    </section>
  );
}
