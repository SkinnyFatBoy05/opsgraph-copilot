from fastapi.testclient import TestClient

from opsgraph.api.app import create_app
from opsgraph.config import Settings


def test_hybrid_chat_returns_evidence_sql_and_trace() -> None:
    with TestClient(create_app(Settings(profile="test"))) as client:
        response = client.post(
            "/api/v1/chat",
            json={
                "domain": "bankops",
                "question": "Which cases are late and what policy applies?",
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "completed"
    assert body["evidence"]
    assert body["sql"]["normalized_sql"].startswith("SELECT")
    assert body["trace"]["tool_call_count"] <= 6
    assert set(body["trace"]["agents"]) == {
        "policy_research",
        "data_analyst",
        "evidence_verifier",
    }
    assert body["correlation_id"].startswith("corr-")


def test_unsupported_chat_abstains_instead_of_inventing() -> None:
    with TestClient(create_app(Settings(profile="test"))) as client:
        response = client.post(
            "/api/v1/chat",
            json={"domain": "bankops", "question": "Write me a poem"},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "manual_review"
    assert body["answer"].startswith("Manual review required")
    assert body["evidence"] == []


def test_identical_question_uses_bounded_response_cache() -> None:
    app = create_app(Settings(profile="test"))
    request = {
        "domain": "bankops",
        "question": "What does the complaint policy require?",
    }
    with TestClient(app) as client:
        first = client.post("/api/v1/chat", json=request).json()
        second = client.post("/api/v1/chat", json=request).json()

    assert first["trace"]["cached"] is False
    assert second["trace"]["cached"] is True
    assert first["correlation_id"] != second["correlation_id"]


def test_chat_rejects_oversized_question() -> None:
    with TestClient(create_app(Settings(profile="test"))) as client:
        response = client.post(
            "/api/v1/chat",
            json={"domain": "bankops", "question": "x" * 2_001},
        )

    assert response.status_code == 422
