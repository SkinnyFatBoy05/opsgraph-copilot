from pathlib import Path

import pytest

from opsgraph.analytics_sql.executors import ReadOnlySqlExecutor
from opsgraph.analytics_sql.schemas import BANKOPS_SEMANTIC_SCHEMA
from opsgraph.domains.bankops import BankOpsDomain
from opsgraph.domains.bankops.seed import seed_bankops
from opsgraph.orchestration.graph import GraphDependencies
from opsgraph.orchestration.service import OpsGraphService
from opsgraph.providers.fake import DeterministicFakeModel
from opsgraph.retrieval.embeddings import HashingEmbeddingProvider
from opsgraph.retrieval.faiss_store import FaissVectorStore
from opsgraph.retrieval.loaders import load_documents
from opsgraph.retrieval.service import RetrievalService
from opsgraph.tools.bankops import build_bankops_registry


@pytest.mark.integration
async def test_hybrid_bankops_graph_returns_policy_and_sql_evidence(tmp_path: Path) -> None:
    import sqlite3

    database = tmp_path / "bankops.sqlite"
    with sqlite3.connect(database) as connection:
        seed_bankops(connection)

    retrieval = RetrievalService(
        embeddings=HashingEmbeddingProvider(dimension=128),
        store=FaissVectorStore(dimension=128),
    )
    documents = load_documents(BankOpsDomain().documents_path, "bankops")
    await retrieval.ingest(documents)
    sql_executor = ReadOnlySqlExecutor(
        schema=BANKOPS_SEMANTIC_SCHEMA,
        sqlite_path=database,
    )
    service = OpsGraphService(
        GraphDependencies(
            model=DeterministicFakeModel(),
            registry=build_bankops_registry(retrieval, sql_executor),
        )
    )

    result = await service.run(
        "bankops",
        "Which open complaint cases are late and what policy applies?",
    )

    assert result.trace.status == "completed"
    assert {evidence.kind for evidence in result.evidence} == {"document", "sql"}
    assert result.answer.verified is True
    assert result.answer.citations
    assert any(
        tool_result.name == "query_cases" and tool_result.status == "succeeded"
        for tool_result in result.tool_results
    )
    sql_result = next(result for result in result.tool_results if result.name == "query_cases")
    assert "case_type = 'complaint'" in sql_result.data["normalized_sql"]
