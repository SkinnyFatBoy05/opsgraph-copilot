import json
from decimal import Decimal

from fastapi.testclient import TestClient

from opsgraph.api.app import create_app
from opsgraph.config import Settings
from opsgraph.evaluation.cases import EvaluationSummary
from opsgraph.evaluation.report import write_reports


def test_latest_evaluation_is_hash_verified_and_read_only(tmp_path) -> None:
    summary = EvaluationSummary(
        provider="fake",
        deterministic=True,
        suite_version="2026-08-08",
        generated_at="2026-08-08T00:00:00+00:00",
        total_cases=1,
        passed_cases=1,
        metrics={"route_accuracy": 1.0},
        release_failures=(),
        estimated_cost_usd=Decimal("0"),
        results=(),
    )
    artifacts = write_reports(summary, tmp_path)
    settings = Settings(profile="test", evaluation_report_path=artifacts.json_path)

    with TestClient(create_app(settings)) as client:
        response = client.get("/api/v1/evaluations/latest")
        mutation = client.post("/api/v1/evaluations/latest")

    assert response.status_code == 200
    assert response.json()["provider"] == "fake"
    assert response.json()["deterministic"] is True
    assert mutation.status_code == 405

    payload = artifacts.json_path.read_bytes()
    artifacts.json_path.write_bytes(payload.replace(b"\n", b"\r\n"))
    with TestClient(create_app(settings)) as client:
        line_ending_only = client.get("/api/v1/evaluations/latest")
    assert line_ending_only.status_code == 200

    artifacts.json_path.write_text(json.dumps({"provider": "tampered"}), encoding="utf-8")
    with TestClient(create_app(settings)) as client:
        tampered = client.get("/api/v1/evaluations/latest")
    assert tampered.status_code == 503
