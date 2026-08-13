import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import { BankOpsWorkspace } from "./BankOpsWorkspace";

const hybridResponse = {
  status: "completed",
  correlation_id: "corr-test",
  answer: "Seven synthetic cases are overdue. Priority complaints require acknowledgement within four business hours.",
  limitations: ["Uses fictional policies and synthetic records; human review is required."],
  evidence: [
    {
      id: "chunk-policy",
      kind: "document",
      title: "Synthetic Complaint SLA",
      text: "Priority complaints require acknowledgement within four business hours.",
      source_uri: null,
      section: "Complaint SLA / Priority",
      effective_date: "2026-01-01",
      score: 0.91,
    },
  ],
  sql: {
    normalized_sql: "SELECT case_id FROM service_cases WHERE status = 'open' LIMIT 200",
    columns: ["case_id"],
    rows: [["CASE-0001"]],
    row_count: 1,
    elapsed_ms: 1.2,
    truncated: false,
  },
  trace: {
    run_id: "run-test",
    route: "hybrid",
    agents: ["policy_research", "data_analyst", "evidence_verifier"],
    tool_call_count: 2,
    tool_calls: [
      { name: "search_policy", status: "succeeded" },
      { name: "query_cases", status: "succeeded" },
    ],
    provider: "fake",
    model: "DeterministicFakeModel",
    started_at: "2026-08-08T01:00:00Z",
    completed_at: "2026-08-08T01:00:01Z",
    estimated_cost_usd: 0,
    cached: false,
  },
  error_code: null,
};

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("BankOpsWorkspace", () => {
  it("shows evidence, SQL, and trace for a hybrid answer", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => hybridResponse,
      }),
    );
    render(<BankOpsWorkspace />);

    await userEvent.click(screen.getByRole("button", { name: /Run analysis/i }));

    expect(await screen.findByText("Synthetic Complaint SLA")).toBeVisible();
    expect(screen.getByText(/Seven synthetic cases are overdue/i)).toBeVisible();
    expect(screen.getByText(/SELECT case_id/i)).toBeVisible();
    await userEvent.click(screen.getByRole("tab", { name: /Agent trace/i }));
    expect(screen.getByText("policy_research")).toBeVisible();
    expect(screen.getByText("evidence_verifier")).toBeVisible();
  });

  it("renders a clear manual-review state", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({
          ...hybridResponse,
          status: "manual_review",
          answer: "Manual review required. This request is outside the supported workflow.",
          evidence: [],
          sql: null,
          error_code: "UNSUPPORTED_REQUEST",
        }),
      }),
    );
    render(<BankOpsWorkspace />);

    await userEvent.click(screen.getByRole("button", { name: /Run analysis/i }));

    expect(await screen.findByText(/Manual review required/i)).toBeVisible();
    expect(screen.getByText("UNSUPPORTED_REQUEST")).toBeVisible();
  });

  it("keeps network failures understandable and retryable", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new Error("offline")));
    render(<BankOpsWorkspace />);

    await userEvent.click(screen.getByRole("button", { name: /Run analysis/i }));

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "The analysis service could not be reached",
    );
    expect(screen.getByRole("button", { name: /Run analysis/i })).toBeEnabled();
  });
});
