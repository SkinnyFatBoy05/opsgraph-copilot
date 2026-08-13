import { render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { EvaluationView } from "./EvaluationView";

const evaluationReport = {
  provider: "fake",
  deterministic: true,
  suite_version: "2026-08-08",
  generated_at: "2026-08-08T02:14:01Z",
  total_cases: 28,
  passed_cases: 28,
  metrics: {
    route_accuracy: 1,
    citation_validity: 1,
    sql_safety: 1,
    mean_latency_ms: 4.9,
  },
  release_failures: [],
  estimated_cost_usd: "0",
  results: [],
};

afterEach(() => vi.unstubAllGlobals());

describe("EvaluationView", () => {
  it("renders verified deterministic metrics and provenance", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => evaluationReport,
      }),
    );

    render(<EvaluationView />);

    expect(await screen.findByText("28 / 28")).toBeVisible();
    expect(screen.getByText("Route accuracy")).toBeVisible();
    expect(screen.getByText("SQL safety")).toBeVisible();
    expect(screen.getByText(/No release-blocking failures/i)).toBeVisible();
    expect(screen.getByText(/deterministic fake provider/i)).toBeVisible();
    expect(screen.getByText(/Suite 2026-08-08/i)).toBeVisible();
  });

  it("shows release blockers instead of hiding them", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({
          ...evaluationReport,
          passed_cases: 27,
          release_failures: ["unknown_citation"],
        }),
      }),
    );

    render(<EvaluationView />);

    expect(await screen.findByText("unknown citation")).toBeVisible();
  });
});
