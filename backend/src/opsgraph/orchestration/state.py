"""Typed shared state for the OpsGraph workflow."""

import operator
from datetime import datetime
from typing import Annotated, TypedDict

from opsgraph.contracts.evidence import DomainName, EvidenceRef
from opsgraph.contracts.runs import DraftAnswer, RouteKind, RunStatus, VerifiedAnswer
from opsgraph.contracts.tools import AgentName, ToolCall, ToolResult


class OpsGraphState(TypedDict, total=False):
    run_id: str
    domain: DomainName
    question: str
    started_at: datetime
    route: RouteKind
    route_reason: str
    status: RunStatus
    error_code: str
    error_message: str
    agents: Annotated[tuple[AgentName, ...], operator.add]
    evidence: Annotated[tuple[EvidenceRef, ...], operator.add]
    tool_calls: Annotated[tuple[ToolCall, ...], operator.add]
    tool_results: Annotated[tuple[ToolResult, ...], operator.add]
    draft_answer: DraftAnswer
    answer: VerifiedAnswer
    correction_count: int
