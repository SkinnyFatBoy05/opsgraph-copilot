export type DomainName = "bankops" | "awardlens";
export type RunStatus =
  | "running"
  | "completed"
  | "completed_with_fallback"
  | "manual_review"
  | "failed";

export interface ChatRequest {
  domain: DomainName;
  question: string;
}

export interface Evidence {
  id: string;
  kind: "document" | "sql" | "calculation";
  title: string | null;
  text: string;
  source_uri: string | null;
  section: string | null;
  effective_date: string | null;
  score: number | null;
}

export interface SqlResult {
  normalized_sql: string;
  columns: string[];
  rows: unknown[][];
  row_count: number;
  elapsed_ms: number;
  truncated: boolean;
}

export interface ToolTrace {
  name: string;
  status: "succeeded" | "rejected" | "failed";
}

export interface RunTrace {
  run_id: string;
  route: "rag" | "sql" | "hybrid" | "calculator" | "unsupported";
  agents: string[];
  tool_call_count: number;
  tool_calls: ToolTrace[];
  provider: string;
  model: string;
  started_at: string;
  completed_at: string | null;
  estimated_cost_usd: number;
  cached: boolean;
}

export interface ChatResponse {
  status: RunStatus;
  correlation_id: string;
  answer: string;
  limitations: string[];
  evidence: Evidence[];
  sql: SqlResult | null;
  trace: RunTrace;
  error_code: string | null;
}

export interface RuntimeConfig {
  profile: "test" | "local" | "aws-demo";
  model_provider: "fake" | "ollama" | "bedrock";
  domains: DomainName[];
  local_ingestion_enabled: boolean;
  max_tool_calls: number;
  synthetic_only: true;
}

export interface IngestionResult {
  source_id: string;
  source_hash: string;
  chunk_count: number;
}

export interface EvaluationReport {
  provider: string;
  deterministic: boolean;
  suite_version: string;
  generated_at: string;
  total_cases: number;
  passed_cases: number;
  metrics: Record<string, number>;
  release_failures: string[];
  estimated_cost_usd: string;
  results: unknown[];
}

export interface AwardLensCalculationLine {
  description: string;
  day_type: string;
  minutes: number;
  base_rate_cents: number;
  multiplier: string;
  amount_cents: number;
}

export interface AwardLensFinding {
  record_id: string;
  employee_id: string;
  status: "calculated" | "manual_review";
  calculation_lines: AwardLensCalculationLine[];
  expected_gross_cents: number | null;
  paid_gross_cents: number;
  variance_cents: number | null;
  liability_cents: number | null;
  reasons: string[];
  rule_version: string;
  source_ids: string[];
}

export interface AwardLensAudit {
  audit_id: string;
  created_at: string;
  rule_version: string;
  verification_status: "verified_official" | "fictional_demo";
  source_ids: string[];
  record_count: number;
  calculated_count: number;
  manual_review_count: number;
  total_expected_gross_cents: number;
  total_paid_gross_cents: number;
  total_liability_cents: number;
  input_sha256: string;
  findings: AwardLensFinding[];
  limitations: string[];
}
