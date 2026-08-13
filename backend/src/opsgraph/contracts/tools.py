"""Agent task and tool-call contracts."""

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from opsgraph.contracts.evidence import DomainName, EvidenceRef

AgentName = Literal[
    "supervisor",
    "policy_research",
    "data_analyst",
    "domain_calculation",
    "evidence_verifier",
]
ToolStatus = Literal["succeeded", "rejected", "failed"]


class ToolDefinition(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str = Field(min_length=1)
    description: str = Field(min_length=1)
    input_schema: dict[str, Any]
    allowed_domains: tuple[DomainName, ...]


class ToolCall(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    arguments: dict[str, Any]

    @field_validator("arguments", mode="before")
    @classmethod
    def copy_arguments(cls, value: dict[str, Any]) -> dict[str, Any]:
        return dict(value)


class ToolResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    call_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    status: ToolStatus
    data: dict[str, Any] = Field(default_factory=dict)
    evidence: tuple[EvidenceRef, ...] = ()
    error_code: str | None = None


class AgentTask(BaseModel):
    model_config = ConfigDict(frozen=True)

    agent: AgentName
    domain: DomainName
    question: str = Field(min_length=1)
    context: tuple[EvidenceRef, ...] = ()
