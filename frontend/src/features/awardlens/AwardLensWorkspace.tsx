import { Calculator, FileSearch, LoaderCircle, ShieldCheck, Upload } from "lucide-react";
import { useState } from "react";

import { apiClient } from "../../api/client";
import type { AwardLensAudit, ChatResponse, RuntimeConfig } from "../../api/types";
import { AnswerPanel } from "../../components/AnswerPanel";
import { SqlPanel } from "../../components/SqlPanel";
import { TracePanel } from "../../components/TracePanel";

const defaultQuestion = "How many audit findings need manual review and what policy applies?";

function money(cents: number | null): string {
  if (cents === null) return "Manual review";
  return new Intl.NumberFormat("en-AU", { style: "currency", currency: "AUD" }).format(cents / 100);
}

export function AwardLensWorkspace({ config }: { config?: RuntimeConfig | null }) {
  const [audit, setAudit] = useState<AwardLensAudit | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [file, setFile] = useState<File | null>(null);
  const [token, setToken] = useState("");
  const [question, setQuestion] = useState(defaultQuestion);
  const [answer, setAnswer] = useState<ChatResponse | null>(null);
  const [asking, setAsking] = useState(false);
  const [questionError, setQuestionError] = useState<string | null>(null);
  const [reportUrl, setReportUrl] = useState("/api/v1/awardlens/demo-report");

  const local = config?.profile === "local";

  async function loadDemo() {
    setBusy(true);
    setError(null);
    try {
      setAudit(await apiClient.awardLensDemo());
      setReportUrl("/api/v1/awardlens/demo-report");
    } catch {
      setError("The synthetic demo audit could not be loaded.");
    } finally {
      setBusy(false);
    }
  }

  async function uploadAudit() {
    if (!file) {
      setError("Choose a synthetic payroll CSV first.");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const created = await apiClient.createAwardLensAudit(file, token);
      setAudit(created);
      setReportUrl(`/api/v1/awardlens/audits/${created.audit_id}/report`);
    } catch {
      setError("The CSV audit could not be created. Check the schema and local token.");
    } finally {
      setBusy(false);
    }
  }

  async function askAwardLens() {
    setAsking(true);
    setQuestionError(null);
    try {
      setAnswer(await apiClient.chat({ domain: "awardlens", question }));
    } catch {
      setQuestionError("AwardLens could not run the grounded question.");
    } finally {
      setAsking(false);
    }
  }

  return (
    <main className="awardlens-workspace">
      <header className="awardlens-heading">
        <div>
          <p className="eyebrow">Deterministic payroll audit</p>
          <h1>AwardLens AU</h1>
          <p>Compare synthetic shifts with a deliberately narrow, source-versioned rule set.</p>
        </div>
        <div className="awardlens-actions">
          <button type="button" className="secondary-action" onClick={loadDemo} disabled={busy}>
            {busy ? <LoaderCircle className="spin" aria-hidden="true" /> : <FileSearch aria-hidden="true" />}
            Load demo payroll
          </button>
          {audit ? <a className="report-link" href={reportUrl} target="_blank" rel="noreferrer">Open audit report</a> : null}
        </div>
      </header>

      {local ? (
        <section className="awardlens-upload" aria-labelledby="upload-heading">
          <div><Upload aria-hidden="true" /><h2 id="upload-heading">Local CSV audit</h2></div>
          <label>Synthetic payroll CSV<input type="file" accept=".csv,text/csv" onChange={(event) => setFile(event.target.files?.[0] ?? null)} /></label>
          <label>Local administration token<input type="password" value={token} onChange={(event) => setToken(event.target.value)} /></label>
          <button type="button" onClick={uploadAudit} disabled={busy}>Audit CSV</button>
        </section>
      ) : null}

      {error ? <p className="awardlens-error" role="alert">{error}</p> : null}

      {audit ? (
        <section className="audit-results" aria-labelledby="audit-results-heading">
          <div className="audit-title-row">
            <div><p className="eyebrow">Rule {audit.rule_version}</p><h2 id="audit-results-heading">Audit results</h2></div>
            <span><ShieldCheck aria-hidden="true" /> {audit.verification_status.replaceAll("_", " ")}</span>
          </div>
          <div className="audit-summary-grid">
            <div><span>Records</span><strong>{audit.record_count}</strong></div>
            <div><span>Calculated</span><strong>{audit.calculated_count}</strong></div>
            <div><span>Manual review</span><strong>{audit.manual_review_count}</strong></div>
            <div><span>Potential difference</span><strong>{money(audit.total_liability_cents)}</strong></div>
          </div>
          <div className="award-table-scroll" tabIndex={0} aria-label="Scrollable AwardLens findings">
            <table>
              <thead><tr><th>Record</th><th>Status</th><th>Expected</th><th>Paid</th><th>Difference</th></tr></thead>
              <tbody>
                {audit.findings.map((finding) => (
                  <tr key={finding.record_id}>
                    <td>{finding.record_id}</td>
                    <td><span className={`finding-status finding-${finding.status}`}>{finding.status === "manual_review" ? "Manual review" : "Calculated"}</span></td>
                    <td>{money(finding.expected_gross_cents)}</td>
                    <td>{money(finding.paid_gross_cents)}</td>
                    <td>{money(finding.liability_cents)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="award-limitations">{audit.limitations.map((item) => <span key={item}>{item}</span>)}</div>

          <section className="award-question" aria-labelledby="award-question-heading">
            <div><Calculator aria-hidden="true" /><h2 id="award-question-heading">Ask about the findings</h2></div>
            <textarea aria-label="Question for AwardLens" value={question} onChange={(event) => setQuestion(event.target.value)} />
            <button type="button" onClick={askAwardLens} disabled={asking || question.trim().length < 3}>Ask AwardLens</button>
          </section>
          <AnswerPanel response={answer} busy={asking} error={questionError} />
          {answer ? (
            <div className="award-answer-details">
              <details open><summary>Generated SQL</summary><SqlPanel sql={answer.sql} /></details>
              <details><summary>Agent trace</summary><TracePanel trace={answer.trace} /></details>
            </div>
          ) : null}
        </section>
      ) : (
        <section className="awardlens-empty">
          <ShieldCheck aria-hidden="true" />
          <h2>Start with synthetic data</h2>
          <p>Load the bundled payroll to inspect deterministic calculations, manual-review boundaries, and source-linked explanations.</p>
        </section>
      )}
    </main>
  );
}
