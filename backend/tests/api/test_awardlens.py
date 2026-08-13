from pathlib import Path

from fastapi.testclient import TestClient

from opsgraph.api.app import create_app
from opsgraph.config import Settings


PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEMO_CSV = PROJECT_ROOT / "data" / "awardlens" / "seed" / "demo-payroll.csv"


def test_aws_profile_exposes_only_precomputed_demo_audit() -> None:
    with TestClient(create_app(Settings(profile="aws-demo"))) as client:
        demo = client.get("/api/v1/awardlens/demo-audit")
        report = client.get("/api/v1/awardlens/demo-report")
        create = client.post(
            "/api/v1/awardlens/audits",
            files={"file": ("payroll.csv", DEMO_CSV.read_bytes(), "text/csv")},
        )

    assert demo.status_code == 200
    assert demo.json()["record_count"] == 8
    assert report.status_code == 200
    assert create.status_code == 404


def test_local_profile_creates_reads_and_reports_audit() -> None:
    settings = Settings(profile="local", local_admin_token="awardlens-test-token")
    with TestClient(create_app(settings)) as client:
        created = client.post(
            "/api/v1/awardlens/audits",
            headers={"X-Local-Admin-Token": "awardlens-test-token"},
            files={"file": ("payroll.csv", DEMO_CSV.read_bytes(), "text/csv")},
        )
        audit_id = created.json()["audit_id"]
        fetched = client.get(f"/api/v1/awardlens/audits/{audit_id}")
        report = client.get(f"/api/v1/awardlens/audits/{audit_id}/report")

    assert created.status_code == 201
    assert fetched.status_code == 200
    assert fetched.json() == created.json()
    assert report.status_code == 200
    assert report.headers["content-type"].startswith("text/html")
    assert "<script" not in report.text.casefold()
    assert "src=" not in report.text.casefold()
    assert "MA000004" in report.text


def test_local_audit_requires_admin_token() -> None:
    with TestClient(create_app(Settings(profile="local"))) as client:
        response = client.post(
            "/api/v1/awardlens/audits",
            files={"file": ("payroll.csv", DEMO_CSV.read_bytes(), "text/csv")},
        )

    assert response.status_code == 401
