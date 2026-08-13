"""Bounded in-memory storage for safe operational run summaries."""

from collections import deque
from dataclasses import asdict, dataclass
from hashlib import sha256
from threading import Lock

from opsgraph.contracts.runs import RunResult


@dataclass(frozen=True)
class SafeRunSummary:
    run_id: str
    correlation_id: str
    domain: str
    question_hash: str
    route: str
    status: str
    provider: str
    model: str
    agents: tuple[str, ...]
    tool_names: tuple[str, ...]
    evidence_ids: tuple[str, ...]
    estimated_cost_usd: str
    cached: bool

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


class RunRecorder:
    """Record only allowlisted metadata; never prompts, answers, or tool arguments."""

    def __init__(self, max_runs: int = 200) -> None:
        if max_runs < 1:
            raise ValueError("max_runs must be positive")
        self._runs: deque[SafeRunSummary] = deque(maxlen=max_runs)
        self._lock = Lock()

    def record(
        self,
        result: RunResult,
        *,
        correlation_id: str,
        cached: bool,
    ) -> SafeRunSummary:
        trace = result.trace
        summary = SafeRunSummary(
            run_id=trace.run_id,
            correlation_id=correlation_id,
            domain=trace.domain,
            question_hash=sha256(trace.question.encode("utf-8")).hexdigest(),
            route=trace.route,
            status=trace.status,
            provider=trace.provider,
            model=trace.model,
            agents=tuple(trace.agents),
            tool_names=tuple(call.name for call in trace.tool_calls),
            evidence_ids=tuple(item.id for item in result.evidence),
            estimated_cost_usd=str(trace.estimated_cost_usd),
            cached=cached,
        )
        with self._lock:
            self._runs.append(summary)
        return summary

    def latest(self) -> SafeRunSummary | None:
        with self._lock:
            return self._runs[-1] if self._runs else None

    def snapshot(self) -> tuple[SafeRunSummary, ...]:
        with self._lock:
            return tuple(self._runs)
