"""Read-only BankOps tools and their specialist permissions."""

import json
from datetime import UTC, datetime
from hashlib import sha256

from opsgraph.analytics_sql.executors import ReadOnlySqlExecutor
from opsgraph.contracts.evidence import EvidenceRef
from opsgraph.contracts.tools import ToolCall, ToolDefinition, ToolResult
from opsgraph.domains.bankops.metrics import business_hours_between
from opsgraph.retrieval.service import RetrievalService
from opsgraph.tools.registry import ToolRegistry

DEMO_AS_OF = datetime(2026, 8, 7, 12, 0, tzinfo=UTC)


def build_bankops_registry(
    retrieval: RetrievalService,
    sql_executor: ReadOnlySqlExecutor,
) -> ToolRegistry:
    registry = ToolRegistry()

    async def search_policy(call: ToolCall) -> ToolResult:
        query = str(call.arguments.get("query", "")).strip()
        hits = await retrieval.search(domain="bankops", query=query, top_k=5)
        evidence = tuple(
            EvidenceRef(
                id=hit.id,
                domain="bankops",
                kind="document",
                title=hit.document_id,
                text=hit.text,
                source_uri=hit.source_uri,
                section=hit.heading,
                effective_date=hit.effective_date,
                score=hit.score,
                metadata={
                    **hit.metadata,
                    "document_id": hit.document_id,
                    "version": hit.version,
                    "owner": hit.owner,
                },
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

    async def query_cases(call: ToolCall) -> ToolResult:
        question = str(call.arguments.get("query", ""))
        sql = _bankops_sql_for(question)
        result = await sql_executor.execute(sql)
        serialized = {
            "columns": result.columns,
            "rows": result.rows,
            "row_count": result.row_count,
        }
        numeric_facts = {
            "overdue_open_cases": (
                int(result.rows[0][0])
                if result.columns and result.columns[0] == "overdue_count" and result.rows
                else result.row_count
            )
        }
        evidence_id = f"sql-{sha256(result.normalized_sql.encode()).hexdigest()[:20]}"
        evidence = EvidenceRef(
            id=evidence_id,
            domain="bankops",
            kind="sql",
            title="Read-only BankOps query",
            text=json.dumps(serialized, default=str, separators=(",", ":")),
            metadata={
                "normalized_sql": result.normalized_sql,
                "columns": result.columns,
                "row_count": result.row_count,
                "elapsed_ms": round(result.elapsed_ms, 3),
                "truncated": result.truncated,
                "numeric_facts": numeric_facts,
            },
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
            },
            evidence=(evidence,),
        )

    async def calculate_metrics(call: ToolCall) -> ToolResult:
        result = await sql_executor.execute(
            """
            SELECT case_id, opened_at, due_at
            FROM service_cases
            WHERE status = 'open' AND due_at < '2026-08-07T12:00:00+00:00'
            ORDER BY due_at
            LIMIT 5
            """
        )
        calculations = tuple(
            {
                "case_id": row[0],
                "business_hours_open": str(
                    business_hours_between(datetime.fromisoformat(row[1]), DEMO_AS_OF)
                ),
            }
            for row in result.rows
        )
        text = json.dumps({"as_of": DEMO_AS_OF.isoformat(), "cases": calculations})
        evidence = EvidenceRef(
            id=f"calculation-{sha256(text.encode()).hexdigest()[:20]}",
            domain="bankops",
            kind="calculation",
            title="Deterministic business-hours calculation",
            text=text,
            metadata={"as_of": DEMO_AS_OF.isoformat(), "case_count": len(calculations)},
        )
        return ToolResult(
            call_id=call.id,
            name=call.name,
            status="succeeded",
            data={"calculations": calculations},
            evidence=(evidence,),
        )

    registry.register(
        ToolDefinition(
            name="search_policy",
            description="Search versioned synthetic BankOps policy documents.",
            input_schema={
                "type": "object",
                "properties": {"query": {"type": "string"}},
                "required": ["query"],
            },
            allowed_domains=("bankops",),
        ),
        allowed_agents=frozenset({"policy_research"}),
        handler=search_policy,
    )
    registry.register(
        ToolDefinition(
            name="query_cases",
            description="Generate, validate, and execute one read-only BankOps analytics query.",
            input_schema={
                "type": "object",
                "properties": {"query": {"type": "string"}},
                "required": ["query"],
            },
            allowed_domains=("bankops",),
        ),
        allowed_agents=frozenset({"data_analyst"}),
        handler=query_cases,
    )
    registry.register(
        ToolDefinition(
            name="calculate_bankops_metrics",
            description="Calculate deterministic elapsed business hours for selected cases.",
            input_schema={
                "type": "object",
                "properties": {"query": {"type": "string"}},
                "required": ["query"],
            },
            allowed_domains=("bankops",),
        ),
        allowed_agents=frozenset({"domain_calculation"}),
        handler=calculate_metrics,
    )
    return registry


def _bankops_sql_for(question: str) -> str:
    normalized = question.casefold()
    if "how many" in normalized or "count" in normalized:
        return """
            SELECT COUNT(*) AS overdue_count
            FROM service_cases
            WHERE status = 'open' AND due_at < '2026-08-07T12:00:00+00:00'
        """
    if "loan" in normalized:
        return """
            SELECT application_id, customer_id, submitted_at, exception_reason
            FROM loan_applications
            WHERE status = 'pending' AND submitted_at < '2026-08-05T12:00:00+00:00'
            ORDER BY submitted_at
        """
    complaint_filter = "AND case_type = 'complaint'" if "complaint" in normalized else ""
    return f"""
        SELECT case_id, case_type, priority, due_at, assigned_team
        FROM service_cases
        WHERE status = 'open'
          AND due_at < '2026-08-07T12:00:00+00:00'
          {complaint_filter}
        ORDER BY due_at
    """
