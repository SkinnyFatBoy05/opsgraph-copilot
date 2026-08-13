"""AwardLens retrieval, guarded SQL, and deterministic calculation tools."""

import json
from hashlib import sha256

from opsgraph.analytics_sql.executors import ReadOnlySqlExecutor
from opsgraph.contracts.evidence import EvidenceRef
from opsgraph.contracts.tools import ToolCall, ToolDefinition, ToolResult
from opsgraph.domains.awardlens.models import AuditRun
from opsgraph.retrieval.service import RetrievalService
from opsgraph.tools.registry import ToolRegistry


def register_awardlens_tools(
    registry: ToolRegistry,
    retrieval: RetrievalService,
    sql_executor: ReadOnlySqlExecutor,
    demo_audit: AuditRun,
) -> None:
    async def search_policy(call: ToolCall) -> ToolResult:
        query = str(call.arguments.get("query", "")).strip()
        hits = await retrieval.search(domain="awardlens", query=query, top_k=5)
        evidence = tuple(
            EvidenceRef(
                id=hit.id,
                domain="awardlens",
                kind="document",
                title=hit.document_id,
                text=hit.text,
                source_uri=hit.source_uri,
                section=hit.heading,
                effective_date=hit.effective_date,
                score=hit.score,
                metadata={**hit.metadata, "document_id": hit.document_id, "version": hit.version},
            )
            for hit in hits
        )
        return ToolResult(
            call_id=call.id,
            name=call.name,
            status="succeeded",
            data={"hit_count": len(hits)},
            evidence=evidence,
        )

    async def query_findings(call: ToolCall) -> ToolResult:
        sql = _awardlens_sql_for(str(call.arguments.get("query", "")))
        result = await sql_executor.execute(sql)
        serialized = {
            "columns": result.columns,
            "rows": result.rows,
            "row_count": result.row_count,
        }
        finding_count = (
            int(result.rows[0][0])
            if result.columns and result.columns[0] == "finding_count" and result.rows
            else result.row_count
        )
        evidence = EvidenceRef(
            id=f"sql-{sha256(result.normalized_sql.encode()).hexdigest()[:20]}",
            domain="awardlens",
            kind="sql",
            title="Read-only AwardLens findings query",
            text=json.dumps(serialized, separators=(",", ":"), default=str),
            metadata={"normalized_sql": result.normalized_sql, "row_count": result.row_count},
        )
        return ToolResult(
            call_id=call.id,
            name=call.name,
            status="succeeded",
            data={
                **serialized,
                "normalized_sql": result.normalized_sql,
                "elapsed_ms": result.elapsed_ms,
                "truncated": result.truncated,
                "numeric_facts": {"finding_count": finding_count},
            },
            evidence=(evidence,),
        )

    async def calculate_audit(call: ToolCall) -> ToolResult:
        numeric_facts = {
            "total_expected_gross_cents": demo_audit.total_expected_gross_cents,
            "total_paid_gross_cents": demo_audit.total_paid_gross_cents,
            "total_liability_cents": demo_audit.total_liability_cents,
            "calculated_count": demo_audit.calculated_count,
            "manual_review_count": demo_audit.manual_review_count,
        }
        evidence = EvidenceRef(
            id=f"calculation-{demo_audit.input_sha256[:20]}",
            domain="awardlens",
            kind="calculation",
            title="Deterministic AwardLens demo audit",
            text=json.dumps(numeric_facts, sort_keys=True),
            metadata={"rule_version": demo_audit.rule_version, "source_ids": demo_audit.source_ids},
        )
        return ToolResult(
            call_id=call.id,
            name=call.name,
            status="succeeded",
            data={"numeric_facts": numeric_facts},
            evidence=(evidence,),
        )

    registry.register(
        ToolDefinition(
            name="search_policy",
            description="Search the source-bound AwardLens rule summary.",
            input_schema={"type": "object", "properties": {"query": {"type": "string"}}},
            allowed_domains=("awardlens",),
        ),
        allowed_agents=frozenset({"policy_research"}),
        handler=search_policy,
    )
    registry.register(
        ToolDefinition(
            name="query_award_findings",
            description="Run one guarded read-only query over synthetic AwardLens findings.",
            input_schema={"type": "object", "properties": {"query": {"type": "string"}}},
            allowed_domains=("awardlens",),
        ),
        allowed_agents=frozenset({"data_analyst"}),
        handler=query_findings,
    )
    registry.register(
        ToolDefinition(
            name="award_calculator",
            description="Return immutable deterministic amounts from the synthetic demo audit.",
            input_schema={"type": "object", "properties": {"query": {"type": "string"}}},
            allowed_domains=("awardlens",),
        ),
        allowed_agents=frozenset({"domain_calculation"}),
        handler=calculate_audit,
    )


def _awardlens_sql_for(question: str) -> str:
    normalized = question.casefold()
    if "how many" in normalized or "count" in normalized:
        filter_clause = "WHERE status = 'manual_review'" if "manual review" in normalized else ""
        return f"SELECT COUNT(*) AS finding_count FROM audit_findings {filter_clause}"
    if "manual review" in normalized:
        return """
            SELECT record_id, status, paid_gross_cents, rule_version
            FROM audit_findings
            WHERE status = 'manual_review'
            ORDER BY record_id
        """
    return """
        SELECT record_id, status, expected_gross_cents, paid_gross_cents, liability_cents, rule_version
        FROM audit_findings
        ORDER BY liability_cents DESC, record_id
    """
