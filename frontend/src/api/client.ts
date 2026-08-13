import type {
  AwardLensAudit,
  ChatRequest,
  ChatResponse,
  EvaluationReport,
  IngestionResult,
  RuntimeConfig,
} from "./types";

export class ApiError extends Error {
  constructor(
    message: string,
    public readonly status: number,
  ) {
    super(message);
  }
}

async function responseJson<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let message = `Request failed with status ${response.status}`;
    try {
      const body = (await response.json()) as { detail?: string };
      message = body.detail ?? message;
    } catch {
      // A bounded fallback is clearer than exposing an HTML proxy error.
    }
    throw new ApiError(message, response.status);
  }
  return (await response.json()) as T;
}

export const apiClient = {
  async chat(payload: ChatRequest, signal?: AbortSignal): Promise<ChatResponse> {
    const response = await fetch("/api/v1/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
      signal,
    });
    return responseJson<ChatResponse>(response);
  },

  async config(signal?: AbortSignal): Promise<RuntimeConfig> {
    const response = await fetch("/api/v1/config", { signal });
    return responseJson<RuntimeConfig>(response);
  },

  async latestEvaluation(signal?: AbortSignal): Promise<EvaluationReport> {
    const response = await fetch("/api/v1/evaluations/latest", { signal });
    return responseJson<EvaluationReport>(response);
  },

  async awardLensDemo(signal?: AbortSignal): Promise<AwardLensAudit> {
    const response = await fetch("/api/v1/awardlens/demo-audit", { signal });
    return responseJson<AwardLensAudit>(response);
  },

  async createAwardLensAudit(
    file: File,
    localAdminToken: string,
    signal?: AbortSignal,
  ): Promise<AwardLensAudit> {
    const form = new FormData();
    form.append("file", file);
    const response = await fetch("/api/v1/awardlens/audits", {
      method: "POST",
      headers: { "X-Local-Admin-Token": localAdminToken },
      body: form,
      signal,
    });
    return responseJson<AwardLensAudit>(response);
  },

  async ingestBankOps(
    file: File,
    localAdminToken: string,
    signal?: AbortSignal,
  ): Promise<IngestionResult> {
    const form = new FormData();
    form.append("file", file);
    const response = await fetch("/api/v1/bankops/ingest", {
      method: "POST",
      headers: { "X-Local-Admin-Token": localAdminToken },
      body: form,
      signal,
    });
    return responseJson<IngestionResult>(response);
  },
};
