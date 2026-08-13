"""Central tool allowlist with agent and domain permissions."""

from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from opsgraph.contracts.evidence import DomainName
from opsgraph.contracts.errors import ErrorCode, OpsGraphError
from opsgraph.contracts.tools import AgentName, ToolCall, ToolDefinition, ToolResult
from opsgraph.observability.tracing import traced

ToolHandler = Callable[[ToolCall], Awaitable[ToolResult]]


class ToolPermissionDenied(OpsGraphError):
    def __init__(self, message: str) -> None:
        super().__init__(ErrorCode.TOOL_REJECTED, message, status_code=422)


@dataclass(frozen=True)
class RegisteredTool:
    definition: ToolDefinition
    allowed_agents: frozenset[AgentName]
    handler: ToolHandler


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[tuple[str, DomainName], RegisteredTool] = {}

    def register(
        self,
        definition: ToolDefinition,
        *,
        allowed_agents: frozenset[AgentName],
        handler: ToolHandler,
    ) -> None:
        registered = RegisteredTool(
            definition=definition,
            allowed_agents=allowed_agents,
            handler=handler,
        )
        for domain in definition.allowed_domains:
            key = (definition.name, domain)
            if key in self._tools:
                raise ValueError(f"tool is already registered: {definition.name}/{domain}")
            self._tools[key] = registered

    def definitions_for(
        self,
        agent: AgentName,
        domain: DomainName,
    ) -> tuple[ToolDefinition, ...]:
        return tuple(
            registered.definition
            for (name, registered_domain), registered in self._tools.items()
            if registered_domain == domain and agent in registered.allowed_agents
        )

    async def invoke(
        self,
        agent: AgentName,
        domain: DomainName,
        call: ToolCall,
    ) -> ToolResult:
        registered = self._tools.get((call.name, domain))
        if registered is None:
            raise ToolPermissionDenied(f"unknown tool: {call.name}")
        if agent not in registered.allowed_agents:
            raise ToolPermissionDenied(f"{agent} cannot invoke {call.name}")
        if domain not in registered.definition.allowed_domains:
            raise ToolPermissionDenied(f"{call.name} is not available in {domain}")
        span_name = (
            "opsgraph.calculation"
            if "calculate" in call.name or "calculator" in call.name
            else "opsgraph.tool"
        )
        with traced(
            span_name,
            {"agent": agent, "domain": domain, "tool_name": call.name},
        ):
            return await registered.handler(call)
