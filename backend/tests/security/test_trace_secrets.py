import json

from fastapi.testclient import TestClient

from opsgraph.api.app import create_app
from opsgraph.config import Settings
from opsgraph.observability.tracing import clear_recorded_spans, recorded_spans


def test_request_trace_uses_expected_spans_without_recording_secrets() -> None:
    clear_recorded_spans()
    marker = "do-not-record-this-value"
    with TestClient(create_app(Settings(profile="test"))) as client:
        response = client.post(
            "/api/v1/chat",
            headers={
                "Authorization": f"Bearer {marker}",
                "Cookie": f"session={marker}",
            },
            json={
                "domain": "bankops",
                "question": (
                    "Which open complaint cases are late and what policy applies? "
                    f"{marker}"
                ),
            },
        )

    assert response.status_code == 200
    spans = recorded_spans()
    names = {span.name for span in spans}
    assert {
        "opsgraph.request",
        "opsgraph.route",
        "opsgraph.retrieval",
        "opsgraph.sql.validate",
        "opsgraph.sql.execute",
        "opsgraph.verify",
    } <= names
    serialized = json.dumps(
        [
            {"name": span.name, "attributes": span.attributes}
            for span in spans
        ],
        default=str,
    )
    assert marker not in serialized
    assert marker not in response.text
    assert "question_hash" in serialized
