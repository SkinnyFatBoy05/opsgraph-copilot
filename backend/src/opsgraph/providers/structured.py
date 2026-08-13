"""Shared bounded behavior for providers that return validated JSON."""

from abc import ABC, abstractmethod
from hashlib import sha256
from typing import Any

from pydantic import BaseModel

from opsgraph.contracts.evidence import DomainName
from opsgraph.contracts.runs import DraftAnswer, RouteDecision, SynthesisRequest
from opsgraph.contracts.tools import AgentTask, ToolCall, ToolDefinition


class StructuredAgentModel(ABC):
    """Use an LLM for routing/synthesis while keeping tool execution bounded."""

    provider_name: str
    model_name: str

    async def route(self, question: str, domain: DomainName) -> RouteDecision:
        return await self._structured_completion(
            "Route the request to exactly one supported workflow. Return only valid JSON.",
            {
                "domain": domain,
                "question": question,
                "routes": ["rag", "sql", "hybrid", "calculator", "unsupported"],
            },
            RouteDecision,
        )

    async def choose_tools(
        self,
        task: AgentTask,
        tools: tuple[ToolDefinition, ...],
    ) -> tuple[ToolCall, ...]:
        # Specialists receive only their allow-listed domain tools. Selecting
        # those tools here keeps function calling deterministic and bounded.
        return tuple(
            ToolCall(
                id=f"call-{sha256(f'{task.domain}:{task.agent}:{tool.name}:{task.question}'.encode()).hexdigest()[:12]}",
                name=tool.name,
                arguments={"query": task.question},
            )
            for tool in tools
        )

    async def synthesize(self, request: SynthesisRequest) -> DraftAnswer:
        return await self._structured_completion(
            (
                "Answer only from the supplied evidence. Preserve numeric_facts exactly, "
                "cite only supplied evidence IDs, and return only valid JSON."
            ),
            request.model_dump(mode="json"),
            DraftAnswer,
        )

    @abstractmethod
    async def _structured_completion(
        self,
        system: str,
        payload: dict[str, Any],
        response_model: type[BaseModel],
    ):
        raise NotImplementedError
