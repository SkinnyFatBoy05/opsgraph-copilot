"""Lazy, explicit dependency wiring for each application instance."""

import asyncio
from hashlib import sha256
from pathlib import Path
from tempfile import gettempdir

from fastapi import Request

from opsgraph.analytics_sql.executors import ReadOnlySqlExecutor
from opsgraph.analytics_sql.schemas import BANKOPS_SEMANTIC_SCHEMA
from opsgraph.api.cache import BoundedRunStore, BoundedTtlCache
from opsgraph.api.schemas import ChatResponse
from opsgraph.config import Settings
from opsgraph.contracts.runs import RunResult
from opsgraph.domains.bankops import BankOpsDomain
from opsgraph.domains.awardlens.adapter import (
    AWARDLENS_FINDINGS_SCHEMA,
    AwardLensDomain,
    create_findings_database,
)
from opsgraph.domains.awardlens.audit import run_audit
from opsgraph.domains.awardlens.csv_ingestion import parse_payroll_csv
from opsgraph.domains.awardlens.models import AuditRun, AwardRuleSet
from opsgraph.orchestration.budget import ExecutionBudget
from opsgraph.orchestration.graph import GraphDependencies
from opsgraph.orchestration.service import OpsGraphService
from opsgraph.observability.run_recorder import RunRecorder
from opsgraph.providers.factory import build_agent_model
from opsgraph.retrieval.contracts import SourceDocument
from opsgraph.retrieval.embeddings import HashingEmbeddingProvider
from opsgraph.retrieval.faiss_store import FaissVectorStore
from opsgraph.retrieval.loaders import load_documents
from opsgraph.retrieval.service import RetrievalService
from opsgraph.tools.bankops import build_bankops_registry
from opsgraph.tools.awardlens import register_awardlens_tools


class AppServices:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.response_cache: BoundedTtlCache[RunResult] = BoundedTtlCache(
            max_items=100,
            ttl_seconds=settings.response_cache_seconds,
        )
        self.run_store: BoundedRunStore[ChatResponse] = BoundedRunStore(max_items=100)
        self.run_recorder = RunRecorder(max_runs=200)
        self.awardlens_audits: BoundedRunStore[AuditRun] = BoundedRunStore(max_items=50)
        self._lock = asyncio.Lock()
        self._service: OpsGraphService | None = None
        self._retrieval: RetrievalService | None = None
        self._awardlens_demo: AuditRun | None = None
        self._awardlens_rules: AwardRuleSet | None = None

    async def graph_service(self) -> OpsGraphService:
        if self._service is not None:
            return self._service
        async with self._lock:
            if self._service is None:
                await self._initialize()
        assert self._service is not None
        return self._service

    async def ingest(self, document: SourceDocument) -> int:
        await self.graph_service()
        assert self._retrieval is not None
        return await self._retrieval.ingest((document,))

    def cache_key(self, domain: str, question: str) -> str:
        material = (
            f"{domain}:{self.settings.model_provider}:prompt-v1:"
            f"{question.strip().casefold()}"
        )
        return sha256(material.encode()).hexdigest()

    async def awardlens_demo_audit(self) -> AuditRun:
        await self.graph_service()
        assert self._awardlens_demo is not None
        return self._awardlens_demo

    async def create_awardlens_audit(self, payload: bytes) -> AuditRun:
        await self.graph_service()
        assert self._awardlens_rules is not None
        audit = run_audit(parse_payroll_csv(payload), self._awardlens_rules)
        self.awardlens_audits.set(audit.audit_id, audit)
        return audit

    def get_awardlens_audit(self, audit_id: str) -> AuditRun | None:
        return self.awardlens_audits.get(audit_id)

    async def _initialize(self) -> None:
        project_root = Path(__file__).resolve().parents[4]
        database = self.settings.sqlite_database_path or (
            project_root / "data" / "bankops" / "demo.sqlite"
        )
        embeddings = HashingEmbeddingProvider(dimension=384)
        retrieval = RetrievalService(
            embeddings=embeddings,
            store=FaissVectorStore(dimension=embeddings.dimension),
        )
        awardlens_domain = AwardLensDomain()
        documents = (
            *load_documents(BankOpsDomain().documents_path, "bankops"),
            *load_documents(awardlens_domain.documents_path, "awardlens"),
        )
        await retrieval.ingest(documents)
        sql_executor = ReadOnlySqlExecutor(
            schema=BANKOPS_SEMANTIC_SCHEMA,
            sqlite_path=database,
        )
        registry = build_bankops_registry(retrieval, sql_executor)
        awardlens_rules = awardlens_domain.load_rules()
        awardlens_demo = awardlens_domain.demo_audit()
        findings_path = Path(gettempdir()) / f"opsgraph-awardlens-{awardlens_demo.input_sha256[:16]}.sqlite"
        create_findings_database(awardlens_demo, findings_path)
        awardlens_sql = ReadOnlySqlExecutor(
            schema=AWARDLENS_FINDINGS_SCHEMA,
            sqlite_path=findings_path,
        )
        register_awardlens_tools(registry, retrieval, awardlens_sql, awardlens_demo)
        self._retrieval = retrieval
        self._awardlens_rules = awardlens_rules
        self._awardlens_demo = awardlens_demo
        self._service = OpsGraphService(
            GraphDependencies(
                model=build_agent_model(self.settings),
                registry=registry,
                budget=ExecutionBudget(max_tool_calls=self.settings.max_tool_calls),
            )
        )


def get_services(request: Request) -> AppServices:
    return request.app.state.services


def get_settings_from_request(request: Request) -> Settings:
    return request.app.state.settings
