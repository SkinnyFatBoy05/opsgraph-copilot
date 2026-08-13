from opsgraph.observability.redaction import redact_mapping, sanitize_span_attributes


def test_redacts_nested_secrets_without_mutating_input() -> None:
    value = {
        "authorization": "Bearer secret",
        "nested": {
            "cookie": "session=secret",
            "provider_api_key": "secret-key",
            "question_hash": "safe",
        },
        "items": [{"password": "secret-password"}, "safe"],
    }

    redacted = redact_mapping(value)

    assert redacted == {
        "authorization": "[REDACTED]",
        "nested": {
            "cookie": "[REDACTED]",
            "provider_api_key": "[REDACTED]",
            "question_hash": "safe",
        },
        "items": [{"password": "[REDACTED]"}, "safe"],
    }
    assert value["authorization"] == "Bearer secret"


def test_span_attributes_hash_raw_questions_and_flatten_safe_values() -> None:
    attributes = sanitize_span_attributes(
        {
            "question": "Which cases are overdue?",
            "domain": "bankops",
            "authorization": "Bearer secret",
            "tool_names": ("search_policy", "query_cases"),
        }
    )

    assert "question" not in attributes
    assert len(attributes["question_hash"]) == 64
    assert attributes["question_length"] == 24
    assert attributes["authorization"] == "[REDACTED]"
    assert attributes["tool_names"] == ("search_policy", "query_cases")
