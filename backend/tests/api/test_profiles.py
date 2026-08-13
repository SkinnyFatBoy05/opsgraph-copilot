from fastapi.testclient import TestClient

from opsgraph.api.app import create_app
from opsgraph.config import Settings


def test_aws_profile_hides_run_store_and_ingestion() -> None:
    with TestClient(create_app(Settings(profile="aws-demo"))) as client:
        assert client.get("/api/v1/runs/example").status_code == 404
        assert client.post("/api/v1/bankops/ingest").status_code == 404
        config = client.get("/api/v1/config")

    assert config.status_code == 200
    assert config.json()["local_ingestion_enabled"] is False


def test_local_ingestion_requires_token_and_accepts_synthetic_markdown() -> None:
    settings = Settings(profile="local", local_admin_token="test-local-token")
    with TestClient(create_app(settings)) as client:
        unauthorized = client.post(
            "/api/v1/bankops/ingest",
            files={"file": ("policy.md", b"# Synthetic policy\nEvidence rule.", "text/markdown")},
        )
        accepted = client.post(
            "/api/v1/bankops/ingest",
            headers={"X-Local-Admin-Token": "test-local-token"},
            files={"file": ("policy.md", b"# Synthetic policy\nEvidence rule.", "text/markdown")},
        )

    assert unauthorized.status_code == 401
    assert accepted.status_code == 200
    assert accepted.json()["chunk_count"] == 1
    assert len(accepted.json()["source_hash"]) == 64


def test_local_run_store_exposes_only_completed_safe_response() -> None:
    with TestClient(create_app(Settings(profile="local"))) as client:
        chat = client.post(
            "/api/v1/chat",
            json={"domain": "bankops", "question": "How many cases are overdue?"},
        ).json()
        stored = client.get(f"/api/v1/runs/{chat['trace']['run_id']}")

    assert stored.status_code == 200
    assert stored.json()["trace"]["run_id"] == chat["trace"]["run_id"]
    assert "arguments" not in stored.json()["trace"]["tool_calls"][0]
