from decimal import Decimal

from opsgraph.evaluation.cases import EvaluationResult
from opsgraph.evaluation.metrics import summarize


def case_result(**overrides) -> EvaluationResult:
    values = {
        "case_id": "case-1",
        "domain": "bankops",
        "category": "hybrid",
        "provider": "fake",
        "expected_route": "hybrid",
        "actual_route": "hybrid",
        "expected_status": "completed",
        "actual_status": "completed",
        "citation_ids": ("known",),
        "valid_evidence_ids": ("known",),
        "sql_safety": "safe",
        "sql_executed": True,
        "numeric_preserved": True,
        "unsupported_liability": False,
        "latency_ms": 12.5,
        "input_tokens": 0,
        "output_tokens": 0,
        "estimated_cost_usd": Decimal("0"),
    }
    values.update(overrides)
    return EvaluationResult(**values)


def test_unknown_citation_is_release_failure() -> None:
    summary = summarize(
        [case_result(citation_ids=("missing",), valid_evidence_ids=("known",))]
    )

    assert "unknown_citation" in summary.release_failures


def test_unsafe_sql_execution_is_release_failure() -> None:
    summary = summarize([case_result(sql_safety="rejected", sql_executed=True)])

    assert "unsafe_sql_executed" in summary.release_failures


def test_numeric_mutation_is_release_failure() -> None:
    summary = summarize([case_result(numeric_preserved=False)])

    assert "numeric_value_changed" in summary.release_failures


def test_unsupported_awardlens_liability_is_release_failure() -> None:
    summary = summarize(
        [case_result(domain="awardlens", unsupported_liability=True)]
    )

    assert "unsupported_awardlens_liability" in summary.release_failures


def test_summary_computes_metrics_from_observed_results() -> None:
    summary = summarize(
        [
            case_result(),
            case_result(
                case_id="case-2",
                actual_route="rag",
                citation_ids=(),
                valid_evidence_ids=(),
                sql_safety="not_applicable",
                sql_executed=False,
            ),
        ]
    )

    assert summary.total_cases == 2
    assert summary.metrics["route_accuracy"] == 0.5
    assert summary.metrics["citation_validity"] == 1.0
    assert summary.metrics["mean_latency_ms"] == 12.5
    assert summary.estimated_cost_usd == Decimal("0")
