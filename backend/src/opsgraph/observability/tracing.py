"""OpenTelemetry configuration plus a safe deterministic span recorder."""

import json
import logging
from collections import deque
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from dataclasses import dataclass
from threading import Lock
from time import perf_counter
from typing import Any

from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter

from opsgraph.config import Settings
from opsgraph.observability.redaction import sanitize_span_attributes

LOGGER = logging.getLogger("opsgraph.telemetry")
_RECORDED: deque["SpanRecord"] = deque(maxlen=1_000)
_RECORDED_LOCK = Lock()
_TELEMETRY_LOCK = Lock()
_CONFIGURED_PROVIDER: TracerProvider | None = None


@dataclass(frozen=True)
class SpanRecord:
    name: str
    attributes: dict[str, Any]
    duration_ms: float
    status: str


def configure_telemetry(settings: Settings) -> TracerProvider | None:
    """Configure one process-wide provider when telemetry is enabled."""

    global _CONFIGURED_PROVIDER
    if not settings.telemetry_enabled:
        return None
    with _TELEMETRY_LOCK:
        if _CONFIGURED_PROVIDER is not None:
            return _CONFIGURED_PROVIDER
        provider = TracerProvider(
            resource=Resource.create({"service.name": settings.telemetry_service_name})
        )
        if settings.telemetry_exporter == "otlp":
            from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

            exporter = OTLPSpanExporter(endpoint=settings.otel_exporter_otlp_endpoint)
        else:
            exporter = ConsoleSpanExporter()
        provider.add_span_processor(BatchSpanProcessor(exporter))
        trace.set_tracer_provider(provider)
        _CONFIGURED_PROVIDER = provider
        return provider


@contextmanager
def traced(name: str, attributes: Mapping[str, Any] | None = None) -> Iterator[None]:
    """Create a redacted OTel span and a bounded local proof record."""

    safe_attributes = sanitize_span_attributes(attributes or {})
    otel_attributes = {
        key: _otel_value(value)
        for key, value in safe_attributes.items()
        if value is not None
    }
    started = perf_counter()
    status = "ok"
    tracer = trace.get_tracer("opsgraph")
    try:
        with tracer.start_as_current_span(name, attributes=otel_attributes):
            yield
    except Exception:
        status = "error"
        raise
    finally:
        record = SpanRecord(
            name=name,
            attributes=safe_attributes,
            duration_ms=(perf_counter() - started) * 1_000,
            status=status,
        )
        with _RECORDED_LOCK:
            _RECORDED.append(record)
        if LOGGER.isEnabledFor(logging.DEBUG):
            LOGGER.debug(
                json.dumps(
                    {
                        "span": record.name,
                        "attributes": record.attributes,
                        "duration_ms": round(record.duration_ms, 3),
                        "status": record.status,
                    },
                    default=str,
                )
            )


def recorded_spans() -> tuple[SpanRecord, ...]:
    with _RECORDED_LOCK:
        return tuple(_RECORDED)


def clear_recorded_spans() -> None:
    with _RECORDED_LOCK:
        _RECORDED.clear()


def _otel_value(value: Any) -> Any:
    if isinstance(value, (str, bool, int, float)):
        return value
    if isinstance(value, tuple) and all(isinstance(item, (str, bool, int, float)) for item in value):
        return value
    if isinstance(value, list) and all(isinstance(item, (str, bool, int, float)) for item in value):
        return tuple(value)
    return json.dumps(value, sort_keys=True, default=str)
