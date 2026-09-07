from pathlib import Path

from fastapi.testclient import TestClient

from opsgraph.api.app import create_app
from opsgraph.config import Settings


def test_missing_database_is_not_ready_but_process_is_live(tmp_path: Path) -> None:
    with TestClient(create_app(Settings(sqlite_database_path=tmp_path / "missing.sqlite"))) as client:
        response = client.get("/health/ready")
        assert response.status_code == 503
        assert "missing.sqlite" not in response.text
        assert client.get("/health/live").status_code == 200


def test_invalid_evaluation_report_is_not_ready(tmp_path: Path) -> None:
    report = tmp_path / "invalid.json"
    report.write_text("{}")
    with TestClient(create_app(Settings(evaluation_report_path=report))) as client:
        assert client.get("/health/ready").status_code == 503


def test_bundled_demo_is_ready() -> None:
    with TestClient(create_app(Settings(profile="aws-demo"))) as client:
        assert client.get("/health/ready").status_code == 200


def test_public_demo_does_not_expose_api_explorers() -> None:
    with TestClient(create_app(Settings(profile="aws-demo"))) as client:
        for path in ("/docs", "/redoc", "/openapi.json"):
            assert client.get(path).status_code == 404
