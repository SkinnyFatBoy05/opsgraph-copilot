"""Contracts for routing, synthesis, verification, and observable runs."""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from opsgraph.contracts.evidence import DomainName, EvidenceRef
from opsgraph.contracts.tools import AgentName, ToolCall, ToolResult

RouteKind = Literal["rag", "sql", "hybrid", "calculator", "unsupported"]
RunStatus = Literal[
    "running",
    "completed",
    "completed_with_fallback",
    "manual_review",
    "succeeded",
    "rejected",
    "failed",
]


class RouteDecision(BaseModel):
    model_config = ConfigDict(frozen=True)

    route: RouteKind
    reason: str = Field(min_length=1)


class SynthesisRequest(BaseModel):
    model_config = ConfigDict(frozen=True)

    question: str = Field(min_length=1)
    domain: DomainName
    evidence: tuple[EvidenceRef, ...] = ()
    tool_results: tuple[ToolResult, ...] = ()


class DraftAnswer(BaseModel):
    model_config = ConfigDict(frozen=True)

    text: str = Field(min_length=1)
    citation_ids: tuple[str, ...] = ()
    numeric_facts: dict[str, int | float | str] = Field(default_factory=dict)
    limitations: tuple[str, ...] = ()


class VerifiedAnswer(BaseModel):
    model_config = ConfigDict(frozen=True)

    text: str = Field(min_length=1)
    citations: tuple[EvidenceRef, ...] = ()
    numeric_facts: dict[str, int | float | str] = Field(default_factory=dict)
    limitations: tuple[str, ...] = ()
    verified: bool


class TraceEvent(BaseModel):
    model_config = ConfigDict(frozen=True)

    at: datetime
    agent: AgentName
    event: str = Field(min_length=1)
    detail: dict[str, Any] = Field(default_factory=dict)


class RunTrace(BaseModel):
    model_config = ConfigDict(frozen=True)

    run_id: str = Field(min_length=1)
    domain: DomainName
    question: str = Field(min_length=1)
    route: RouteKind
    status: RunStatus
    started_at: datetime
    completed_at: datetime | None = None
    agents: tuple[AgentName, ...] = ()
    tool_calls: tuple[ToolCall, ...] = Field(default=(), max_length=6)
    tool_results: tuple[ToolResult, ...] = Field(default=(), max_length=6)
    events: tuple[TraceEvent, ...] = ()
    provider: str = "fake"
    model: str = "deterministic"
    estimated_cost_usd: float = Field(default=0, ge=0)


class RunResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    answer: VerifiedAnswer
    trace: RunTrace
    evidence: tuple[EvidenceRef, ...] = ()
    tool_results: tuple[ToolResult, ...] = ()
    error_code: str | None = None
