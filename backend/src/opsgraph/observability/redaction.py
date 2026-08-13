"""Redaction helpers shared by traces, logs, and run summaries."""

from collections.abc import Mapping
from hashlib import sha256
from typing import Any

REDACTED = "[REDACTED]"
SENSITIVE_KEY_PARTS = frozenset(
    {
        "api_key",
        "apikey",
        "authorization",
        "cookie",
        "credential",
        "password",
        "secret",
        "session",
        "set_cookie",
        "token",
    }
)
RAW_TEXT_KEYS = frozenset({"input", "message", "output", "prompt", "query", "question"})


def redact_mapping(data: Mapping[str, Any]) -> dict[str, Any]:
    """Return a deep copy with secret-bearing values replaced."""

    return {str(key): _redact_value(str(key), value) for key, value in data.items()}


def sanitize_span_attributes(data: Mapping[str, Any]) -> dict[str, Any]:
    """Convert raw telemetry fields into bounded, non-sensitive attributes."""

    sanitized: dict[str, Any] = {}
    for key, value in redact_mapping(data).items():
        normalized = _normalize_key(key)
        if normalized in RAW_TEXT_KEYS and isinstance(value, str) and value != REDACTED:
            sanitized[f"{normalized}_hash"] = sha256(value.encode("utf-8")).hexdigest()
            sanitized[f"{normalized}_length"] = len(value)
            continue
        sanitized[key] = value
    return sanitized


def _redact_value(key: str, value: Any) -> Any:
    if _is_sensitive_key(key):
        return REDACTED
    if isinstance(value, Mapping):
        return redact_mapping(value)
    if isinstance(value, tuple):
        return tuple(_redact_value("", item) for item in value)
    if isinstance(value, list):
        return [_redact_value("", item) for item in value]
    if isinstance(value, set):
        return tuple(sorted((_redact_value("", item) for item in value), key=str))
    return value


def _is_sensitive_key(key: str) -> bool:
    normalized = _normalize_key(key)
    return any(part in normalized for part in SENSITIVE_KEY_PARTS)


def _normalize_key(key: str) -> str:
    return key.casefold().replace("-", "_").replace(".", "_")
