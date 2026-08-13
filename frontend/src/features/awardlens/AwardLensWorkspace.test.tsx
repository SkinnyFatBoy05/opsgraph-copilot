import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import type { RuntimeConfig } from "../../api/types";
import { AwardLensWorkspace } from "./AwardLensWorkspace";

const demoAudit = {
  audit_id: "audit-demo",
  created_at: "2026-08-08T00:00:00Z",
  rule_version: "2026.07.01",
  verification_status: "verified_official",
  source_ids: ["FWC-MA000004-2026"],
  record_count: 8,
  calculated_count: 6,
  manual_review_count: 2,
  total_expected_gross_cents: 150000,
  total_paid_gross_cents: 140000,
  total_liability_cents: 10000,
  input_sha256: "a".repeat(64),
  findings: [
    {
      record_id: "SHIFT-001",
      employee_id: "SYN-001",
      status: "calculated",
      calculation_lines: [],
      expected_gross_cents: 22248,
      paid_gross_cents: 20000,
      variance_cents: 2248,
      liability_cents: 2248,
      reasons: [],
      rule_version: "2026.07.01",
      source_ids: ["FWC-MA000004-2026"],
    },
    {
      record_id: "SHIFT-002",
      employee_id: "SYN-002",
      status: "manual_review",
      calculation_lines: [],
      expected_gross_cents: null,
      paid_gross_cents: 0,
      variance_cents: null,
      liability_cents: null,
      reasons: ["Classification is outside the supported scope."],
      rule_version: "2026.07.01",
      source_ids: ["FWC-MA000004-2026"],
    },
  ],
  limitations: ["Synthetic demonstration only; not legal or payroll advice."],
};

const awsConfig: RuntimeConfig = {
  profile: "aws-demo",
  model_provider: "fake",
  domains: ["bankops", "awardlens"],
  local_ingestion_enabled: false,
  max_tool_calls: 6,
  synthetic_only: true,
};

afterEach(() => vi.unstubAllGlobals());

describe("AwardLensWorkspace", () => {
  it("loads and explains the precomputed synthetic audit", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({ok: true, json: async () => demoAudit}),
    );
    render(<AwardLensWorkspace config={awsConfig} />);

    await userEvent.click(screen.getByRole("button", { name: /Load demo payroll/i }));

    expect(await screen.findByText("$100.00")).toBeVisible();
    expect(screen.getByText("SHIFT-001")).toBeVisible();
    expect(screen.getAllByText("Manual review").length).toBeGreaterThan(0);
    expect(screen.getByText(/not legal or payroll advice/i)).toBeVisible();
    expect(screen.getByRole("link", { name: /Open audit report/i })).toHaveAttribute(
      "href",
      "/api/v1/awardlens/demo-report",
    );
  });

  it("shows CSV upload controls only in the local profile", () => {
    render(<AwardLensWorkspace config={{ ...awsConfig, profile: "local" }} />);

    expect(screen.getByLabelText(/Synthetic payroll CSV/i)).toBeVisible();
    expect(screen.getByLabelText(/Local administration token/i)).toBeVisible();
  });

  it("keeps a locally viewed demo report on the public demo endpoint", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({ok: true, json: async () => demoAudit}),
    );
    render(<AwardLensWorkspace config={{ ...awsConfig, profile: "local" }} />);

    await userEvent.click(screen.getByRole("button", { name: /Load demo payroll/i }));

    expect(await screen.findByRole("link", { name: /Open audit report/i })).toHaveAttribute(
      "href",
      "/api/v1/awardlens/demo-report",
    );
  });
});
