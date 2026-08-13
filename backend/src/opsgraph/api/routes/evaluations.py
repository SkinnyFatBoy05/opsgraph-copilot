"""Read-only access to the latest verified evaluation report."""

from pathlib import Path

from fastapi import APIRouter, Depends

from opsgraph.api.dependencies import get_settings_from_request
from opsgraph.config import Settings
from opsgraph.contracts.errors import ErrorCode, OpsGraphError
from opsgraph.evaluation.cases import EvaluationSummary
from opsgraph.evaluation.report import verify_report

router = APIRouter(prefix="/api/v1/evaluations", tags=["evaluations"])


@router.get("/latest", response_model=EvaluationSummary)
async def latest_evaluation(
    settings: Settings = Depends(get_settings_from_request),
) -> EvaluationSummary:
    report_path = settings.evaluation_report_path or _default_report_path()
    try:
        return verify_report(report_path)
    except (OSError, ValueError) as error:
        raise OpsGraphError(
            ErrorCode.INTERNAL_ERROR,
            "The verified evaluation report is unavailable.",
            status_code=503,
            retryable=True,
        ) from error


def _default_report_path() -> Path:
    return Path(__file__).resolve().parents[5] / "evaluation" / "reports" / "deterministic" / "latest.json"
