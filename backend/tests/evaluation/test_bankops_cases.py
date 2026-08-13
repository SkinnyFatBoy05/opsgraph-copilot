from pathlib import Path

from opsgraph.api.dependencies import AppServices
from opsgraph.config import Settings
from opsgraph.evaluation.cases import load_cases
from opsgraph.evaluation.runner import run_evaluation


PROJECT_ROOT = Path(__file__).resolve().parents[3]


def test_checked_in_suite_has_required_cross_domain_coverage() -> None:
    cases = load_cases(
        (
            PROJECT_ROOT / "evaluation" / "cases" / "bankops.json",
            PROJECT_ROOT / "evaluation" / "cases" / "security.json",
            PROJECT_ROOT / "evaluation" / "cases" / "awardlens.json",
        )
    )

    assert sum(case.suite == "bankops" for case in cases) >= 20
    assert sum(case.suite == "security" for case in cases) >= 8
    assert sum(case.suite == "awardlens" for case in cases) >= 12
    assert len({case.id for case in cases}) == len(cases)


async def test_fake_provider_suite_passes_release_gates() -> None:
    cases = load_cases(
        (
            PROJECT_ROOT / "evaluation" / "cases" / "bankops.json",
            PROJECT_ROOT / "evaluation" / "cases" / "security.json",
            PROJECT_ROOT / "evaluation" / "cases" / "awardlens.json",
        )
    )
    service = await AppServices(Settings(profile="test")).graph_service()

    summary = await run_evaluation(cases, service, provider="fake")

    assert summary.provider == "fake"
    assert summary.deterministic is True
    assert summary.total_cases >= 40
    assert summary.passed_cases == summary.total_cases
    assert summary.release_failures == ()
    assert summary.metrics["route_accuracy"] == 1.0
    assert summary.metrics["sql_safety"] == 1.0
