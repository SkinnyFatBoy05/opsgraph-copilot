"""Provider protocol consumed by the agent graph."""

from typing import Protocol

from opsgraph.contracts.evidence import DomainName
from opsgraph.contracts.runs import DraftAnswer, RouteDecision, SynthesisRequest
from opsgraph.contracts.tools import AgentTask, ToolCall, ToolDefinition


class AgentModel(Protocol):
    provider_name: str
    model_name: str

    async def route(self, question: str, domain: DomainName) -> RouteDecision: ...

    async def choose_tools(
        self,
        task: AgentTask,
        tools: tuple[ToolDefinition, ...],
    ) -> tuple[ToolCall, ...]: ...

    async def synthesize(self, request: SynthesisRequest) -> DraftAnswer: ...
