from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from opsgraph.contracts.evidence import EvidenceRef
from opsgraph.contracts.runs import RunTrace
from opsgraph.contracts.tools import ToolCall


def test_evidence_is_immutable() -> None:
    evidence = EvidenceRef(
        id="bankops:policy:1",
        domain="bankops",
        text="Synthetic rule",
    )

    with pytest.raises(ValidationError):
        evidence.text = "changed"  # type: ignore[misc]


def test_run_trace_rejects_more_than_six_tool_calls() -> None:
    calls = tuple(
        ToolCall(id=f"call-{index}", name="search_policy", arguments={})
        for index in range(7)
    )

    with pytest.raises(ValidationError, match="at most 6 items"):
        RunTrace(
            run_id="run-1",
            domain="bankops",
            question="What happened?",
            route="hybrid",
            status="running",
            started_at=datetime.now(UTC),
            tool_calls=calls,
        )


def test_tool_arguments_are_copied_from_mutable_input() -> None:
    arguments = {"query": "overdue cases"}
    call = ToolCall(id="call-1", name="query_cases", arguments=arguments)

    arguments["query"] = "changed"

    assert call.arguments == {"query": "overdue cases"}
