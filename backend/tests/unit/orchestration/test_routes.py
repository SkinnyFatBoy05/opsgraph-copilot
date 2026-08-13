from pathlib import Path

import pytest

from opsgraph.analytics_sql.executors import ReadOnlySqlExecutor
from opsgraph.analytics_sql.schemas import BANKOPS_SEMANTIC_SCHEMA
from opsgraph.contracts.runs import RouteDecision
from opsgraph.contracts.tools import AgentTask, ToolCall, ToolDefinition
from opsgraph.domains.bankops.seed import seed_bankops
from opsgraph.orchestration.graph import GraphDependencies
from opsgraph.orchestration.service import OpsGraphService
from opsgraph.providers.fake import DeterministicFakeModel
from opsgraph.retrieval.contracts import SourceDocument
from opsgraph.retrieval.embeddings import HashingEmbeddingProvider
from opsgraph.retrieval.faiss_store import FaissVectorStore
from opsgraph.retrieval.service import RetrievalService
from opsgraph.tools.bankops import build_bankops_registry
from opsgraph.tools.registry import ToolPermissionDenied


class ForcedRouteModel(DeterministicFakeModel):
    def __init__(self, route: str) -> None:
        self.forced_route = route

    async def route(self, question, domain):
        return RouteDecision(route=self.forced_route, reason="forced by test")


class OverBudgetModel(ForcedRouteModel):
    async def choose_tools(
        self,
        task: AgentTask,
        tools: tuple[ToolDefinition, ...],
    ) -> tuple[ToolCall, ...]:
        return tuple(
            ToolCall(id=f"call-{index}", name="search_policy", arguments={"query": task.question})
            for index in range(7)
        )


async def build_service(tmp_path: Path, model) -> tuple[OpsGraphService, object]:
    import sqlite3

    database = tmp_path / "bankops.sqlite"
    with sqlite3.connect(database) as connection:
        seed_bankops(connection)
    retrieval = RetrievalService(
        embeddings=HashingEmbeddingProvider(dimension=64),
        store=FaissVectorStore(dimension=64),
    )
    await retrieval.ingest(
        (
            SourceDocument(
                id="complaint-sla",
                domain="bankops",
                text="# Complaint SLA\nPriority complaints require acknowledgement within four business hours.",
            ),
        )
    )
    sql_executor = ReadOnlySqlExecutor(
        schema=BANKOPS_SEMANTIC_SCHEMA,
        sqlite_path=database,
    )
    registry = build_bankops_registry(retrieval, sql_executor)
    dependencies = GraphDependencies(
        model=model,
        registry=registry,
    )
    return OpsGraphService(dependencies), registry


@pytest.mark.parametrize(
    ("route", "question", "expected"),
    [
        ("rag", "What does the complaint policy require?", {"policy_research", "evidence_verifier"}),
        ("sql", "How many cases are overdue?", {"data_analyst", "evidence_verifier"}),
        (
            "hybrid",
            "Which cases are late and what policy applies?",
            {"policy_research", "data_analyst", "evidence_verifier"},
        ),
        (
            "calculator",
            "Calculate elapsed business hours for overdue cases",
            {"domain_calculation", "evidence_verifier"},
        ),
    ],
)
async def test_route_invokes_only_required_specialists(
    tmp_path, route, question, expected
) -> None:
    service, _ = await build_service(tmp_path, ForcedRouteModel(route))

    result = await service.run("bankops", question)

    assert set(result.trace.agents) == expected
    assert result.trace.status == "completed"


async def test_specialists_cannot_invoke_each_others_tools(tmp_path) -> None:
    _, registry = await build_service(tmp_path, ForcedRouteModel("rag"))
    call = ToolCall(id="forbidden", name="query_cases", arguments={"query": "count"})

    with pytest.raises(ToolPermissionDenied):
        await registry.invoke("policy_research", "bankops", call)


async def test_six_call_budget_returns_manual_review(tmp_path) -> None:
    service, _ = await build_service(tmp_path, OverBudgetModel("rag"))

    result = await service.run("bankops", "What is the policy?")

    assert result.trace.status == "manual_review"
    assert result.error_code == "GRAPH_BUDGET_EXCEEDED"
    assert len(result.trace.tool_calls) <= 6
