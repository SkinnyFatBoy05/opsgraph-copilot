import { Braces, Coins, FileText, GitBranch } from "lucide-react";
import { useEffect, useRef, useState } from "react";

import { apiClient } from "../../api/client";
import type { ChatResponse, RuntimeConfig } from "../../api/types";
import { AnswerPanel } from "../../components/AnswerPanel";
import { CostPanel } from "../../components/CostPanel";
import { EvidencePanel } from "../../components/EvidencePanel";
import { IngestionPanel } from "../../components/IngestionPanel";
import { QuestionComposer } from "../../components/QuestionComposer";
import { SqlPanel } from "../../components/SqlPanel";
import { TracePanel } from "../../components/TracePanel";

type DetailTab = "evidence" | "sql" | "trace" | "cost";

interface BankOpsWorkspaceProps {
  config?: RuntimeConfig | null;
}

const DEFAULT_QUESTION = "Which open complaint cases are late and what policy applies?";

export function BankOpsWorkspace({ config = null }: BankOpsWorkspaceProps) {
  const [question, setQuestion] = useState(DEFAULT_QUESTION);
  const [response, setResponse] = useState<ChatResponse | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedEvidence, setSelectedEvidence] = useState<string | null>(null);
  const [activeDetail, setActiveDetail] = useState<DetailTab>("sql");
  const activeRequest = useRef<AbortController | null>(null);

  useEffect(() => () => activeRequest.current?.abort(), []);

  async function runAnalysis() {
    activeRequest.current?.abort();
    const controller = new AbortController();
    activeRequest.current = controller;
    setBusy(true);
    setError(null);
    try {
      const next = await apiClient.chat(
        { domain: "bankops", question: question.trim() },
        controller.signal,
      );
      setResponse(next);
      setSelectedEvidence(
        next.evidence.find((item) => item.kind === "document")?.id
          ?? next.evidence[0]?.id
          ?? null,
      );
      setActiveDetail(next.sql ? "sql" : "evidence");
    } catch (requestError) {
      if (controller.signal.aborted) return;
      setError(
        requestError instanceof Error && requestError.message !== "offline"
          ? requestError.message
          : "The analysis service could not be reached. Check the API and try again.",
      );
    } finally {
      if (!controller.signal.aborted) setBusy(false);
    }
  }

  const tabs = [
    { id: "evidence", label: "Evidence", Icon: FileText },
    { id: "sql", label: "Generated SQL", Icon: Braces },
    { id: "trace", label: "Agent trace", Icon: GitBranch },
    { id: "cost", label: "Cost", Icon: Coins },
  ] as const;

  return (
    <div className="workspace-layout">
      <main className="workspace-primary">
        <header className="workspace-heading">
          <p className="eyebrow">Evidence-first investigation</p>
          <h1>Bank Operations Copilot</h1>
          <p>Ask across synthetic policy and operational data.</p>
        </header>
        <QuestionComposer
          question={question}
          onQuestionChange={setQuestion}
          onSubmit={runAnalysis}
          busy={busy}
        />
        <AnswerPanel response={response} busy={busy} error={error} />
        {response ? (
          <section className="detail-section">
            <div className="detail-tabs" role="tablist" aria-label="Run details">
              {tabs.map(({ id, label, Icon }) => (
                <button
                  key={id}
                  type="button"
                  role="tab"
                  aria-selected={activeDetail === id}
                  className={activeDetail === id ? "detail-tab-active" : ""}
                  onClick={() => setActiveDetail(id)}
                >
                  <Icon aria-hidden="true" size={16} />
                  {label}
                </button>
              ))}
            </div>
            <div className="detail-panel" role="tabpanel">
              {activeDetail === "evidence" ? (
                <p className="mobile-evidence-prompt">Evidence is shown in the source panel below.</p>
              ) : null}
              {activeDetail === "sql" ? <SqlPanel sql={response.sql} /> : null}
              {activeDetail === "trace" ? <TracePanel trace={response.trace} /> : null}
              {activeDetail === "cost" ? <CostPanel trace={response.trace} /> : null}
            </div>
          </section>
        ) : null}
        {config?.local_ingestion_enabled ? <IngestionPanel /> : null}
      </main>
      <aside className={`evidence-inspector ${activeDetail === "evidence" ? "is-mobile-active" : ""}`}>
        <EvidencePanel
          evidence={response?.evidence ?? []}
          selectedId={selectedEvidence}
          onSelect={setSelectedEvidence}
        />
      </aside>
    </div>
  );
}
