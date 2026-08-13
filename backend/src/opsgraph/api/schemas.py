"""Public API schemas; internal prompts and raw tool arguments are excluded."""

from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from opsgraph.contracts.evidence import DomainName, EvidenceKind
from opsgraph.contracts.runs import RouteKind, RunStatus
from opsgraph.contracts.tools import AgentName, ToolStatus


class ChatRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    domain: DomainName
    question: str = Field(min_length=3, max_length=2_000)


class EvidenceResponse(BaseModel):
    id: str
    kind: EvidenceKind
    title: str | None
    text: str
    source_uri: str | None
    section: str | None
    effective_date: date | None
    score: float | None


class SqlResponse(BaseModel):
    normalized_sql: str
    columns: tuple[str, ...]
    rows: tuple[tuple[Any, ...], ...]
    row_count: int
    elapsed_ms: float
    truncated: bool


class ToolTraceResponse(BaseModel):
    name: str
    status: ToolStatus


class TraceResponse(BaseModel):
    run_id: str
    route: RouteKind
    agents: tuple[AgentName, ...]
    tool_call_count: int = Field(ge=0, le=6)
    tool_calls: tuple[ToolTraceResponse, ...]
    provider: str
    model: str
    started_at: datetime
    completed_at: datetime | None
    estimated_cost_usd: float
    cached: bool


class ChatResponse(BaseModel):
    status: RunStatus
    correlation_id: str
    answer: str
    limitations: tuple[str, ...]
    evidence: tuple[EvidenceResponse, ...]
    sql: SqlResponse | None
    trace: TraceResponse
    error_code: str | None = None


class ConfigResponse(BaseModel):
    profile: Literal["test", "local", "aws-demo"]
    model_provider: Literal["fake", "ollama", "bedrock"]
    domains: tuple[DomainName, ...]
    local_ingestion_enabled: bool
    max_tool_calls: int
    synthetic_only: Literal[True] = True


class IngestionResponse(BaseModel):
    source_id: str
    source_hash: str
    chunk_count: int
