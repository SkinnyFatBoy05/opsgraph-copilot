from opsgraph.api.dependencies import AppServices
from opsgraph.config import Settings


async def test_awardlens_hybrid_graph_returns_policy_and_findings_sql() -> None:
    service = await AppServices(Settings(profile="test")).graph_service()

    result = await service.run(
        "awardlens",
        "How many audit findings need manual review and what policy applies?",
    )

    assert result.trace.status == "completed"
    assert result.trace.route == "hybrid"
    assert {item.kind for item in result.evidence} >= {"document", "sql"}
    assert all(item.domain == "awardlens" for item in result.evidence)
    assert {item.name for item in result.tool_results} == {
        "search_policy",
        "query_award_findings",
    }
    assert "finding_count" in result.answer.numeric_facts


async def test_awardlens_calculator_route_uses_deterministic_audit() -> None:
    service = await AppServices(Settings(profile="test")).graph_service()

    result = await service.run(
        "awardlens",
        "Calculate the expected gross pay for the synthetic demo payroll.",
    )

    assert result.trace.status == "completed"
    assert result.trace.route == "calculator"
    calculation = next(item for item in result.tool_results if item.name == "award_calculator")
    assert result.answer.numeric_facts == calculation.data["numeric_facts"]
