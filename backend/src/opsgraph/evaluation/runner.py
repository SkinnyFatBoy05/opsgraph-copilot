"""Deterministic suite runner and command-line entry point."""

import argparse
from decimal import Decimal
from pathlib import Path
from time import perf_counter

from opsgraph.analytics_sql.guard import SqlRejected, validate_readonly_sql
from opsgraph.analytics_sql.schemas import BANKOPS_SEMANTIC_SCHEMA
from opsgraph.api.dependencies import AppServices
from opsgraph.config import Settings
from opsgraph.evaluation.cases import EvaluationCase, EvaluationResult, load_cases
from opsgraph.evaluation.metrics import summarize
from opsgraph.evaluation.report import write_reports
from opsgraph.observability.tracing import traced
from opsgraph.orchestration.service import OpsGraphService


async def run_evaluation(
    cases: tuple[EvaluationCase, ...],
    service: OpsGraphService,
    *,
    provider: str,
):
    results: list[EvaluationResult] = []
    with traced("opsgraph.evaluation", {"provider": provider, "case_count": len(cases)}):
        for case in cases:
            if case.input_sql is not None:
                results.append(_evaluate_sql_attack(case, provider))
            else:
                results.append(await _evaluate_graph_case(case, service, provider))
    return summarize(results, provider=provider)


def _evaluate_sql_attack(case: EvaluationCase, provider: str) -> EvaluationResult:
    started = perf_counter()
    safety = "safe"
    status = "completed"
    failures: tuple[str, ...] = ()
    try:
        validate_readonly_sql(case.input_sql or "", BANKOPS_SEMANTIC_SCHEMA, "sqlite")
    except SqlRejected:
        safety = "rejected"
        status = "rejected"
    if status != case.expected_status:
        failures = ("unexpected_sql_validation",)
    return EvaluationResult(
        case_id=case.id,
        domain=case.domain,
        category=case.category,
        provider=provider,
        expected_route=case.expected_route,
        actual_route="unsupported",
        expected_status=case.expected_status,
        actual_status=status,
        sql_safety=safety,
        sql_executed=False,
        sql_execution_correct=status == case.expected_status,
        latency_ms=(perf_counter() - started) * 1_000,
        estimated_cost_usd=Decimal("0"),
        failures=failures,
    )


async def _evaluate_graph_case(
    case: EvaluationCase,
    service: OpsGraphService,
    provider: str,
) -> EvaluationResult:
    started = perf_counter()
    run = await service.run(case.domain, case.question)
    latency_ms = (perf_counter() - started) * 1_000
    citations = tuple(item.id for item in run.answer.citations)
    valid_ids = tuple(item.id for item in run.evidence)
    sql_results = tuple(
        result
        for result in run.tool_results
        if result.name in {"query_cases", "query_award_findings", "execute_readonly_sql"}
    )
    normalized_sql = " ".join(
        str(result.data.get("normalized_sql", "")) for result in sql_results
    )
    sql_expected = bool(case.expected_sql_contains)
    sql_execution_correct = (
        not sql_expected
        or (
            bool(sql_results)
            and all(fragment.casefold() in normalized_sql.casefold() for fragment in case.expected_sql_contains)
        )
    )
    numeric_preserved = all(
        run.answer.numeric_facts.get(key) == value
        for key, value in case.expected_numeric_facts.items()
    )
    retrieval_hit = len(run.evidence) >= case.expected_min_evidence
    abstention_correct = (
        run.trace.status == "manual_review"
        if case.expected_status == "manual_review"
        else True
    )
    failures = tuple(
        failure
        for condition, failure in (
            (run.trace.route != case.expected_route, "route_mismatch"),
            (run.trace.status != case.expected_status, "status_mismatch"),
            (not retrieval_hit, "retrieval_miss"),
            (not sql_execution_correct, "sql_result_mismatch"),
            (not numeric_preserved, "numeric_mismatch"),
        )
        if condition
    )
    return EvaluationResult(
        case_id=case.id,
        domain=case.domain,
        category=case.category,
        provider=provider,
        expected_route=case.expected_route,
        actual_route=run.trace.route,
        expected_status=case.expected_status,
        actual_status=run.trace.status,
        citation_ids=citations,
        valid_evidence_ids=valid_ids,
        retrieval_hit=retrieval_hit,
        sql_safety="safe" if sql_results else "not_applicable",
        sql_executed=bool(sql_results),
        sql_execution_correct=sql_execution_correct,
        numeric_preserved=numeric_preserved,
        abstention_correct=abstention_correct,
        latency_ms=latency_ms,
        estimated_cost_usd=Decimal(str(run.trace.estimated_cost_usd)),
        failures=failures,
    )


async def _main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--provider", default="fake", choices=("fake",))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    project_root = Path(__file__).resolve().parents[4]
    cases = load_cases(
        (
            project_root / "evaluation" / "cases" / "bankops.json",
            project_root / "evaluation" / "cases" / "security.json",
            project_root / "evaluation" / "cases" / "awardlens.json",
        )
    )
    service = await AppServices(Settings(profile="test", model_provider=args.provider)).graph_service()
    summary = await run_evaluation(cases, service, provider=args.provider)
    artifacts = write_reports(summary, args.output)
    print(artifacts.json_path)


if __name__ == "__main__":
    import asyncio

    asyncio.run(_main())
