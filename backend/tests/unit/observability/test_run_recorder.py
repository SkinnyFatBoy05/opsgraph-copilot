import json
from datetime import UTC, datetime

from opsgraph.contracts.evidence import EvidenceRef
from opsgraph.contracts.runs import RunResult, RunTrace, VerifiedAnswer
from opsgraph.contracts.tools import ToolCall, ToolResult
from opsgraph.observability.run_recorder import RunRecorder


def test_run_recorder_keeps_only_allowlisted_metadata() -> None:
    marker = "private-run-value"
    evidence = EvidenceRef(
        id="evidence-1",
        domain="bankops",
        text=f"Evidence containing {marker}",
    )
    call = ToolCall(
        id="call-1",
        name="search_policy",
        arguments={"query": marker, "authorization": marker},
    )
    result = ToolResult(
        call_id=call.id,
        name=call.name,
        status="succeeded",
        data={"raw": marker},
        evidence=(evidence,),
    )
    at = datetime(2026, 8, 8, tzinfo=UTC)
    run = RunResult(
        answer=VerifiedAnswer(text=f"Answer {marker}", verified=True),
        trace=RunTrace(
            run_id="run-1",
            domain="bankops",
            question=f"Question {marker}",
            route="rag",
            status="completed",
            started_at=at,
            completed_at=at,
            agents=("policy_research",),
            tool_calls=(call,),
            tool_results=(result,),
            provider="fake",
            model="deterministic-v1",
        ),
        evidence=(evidence,),
        tool_results=(result,),
    )

    recorder = RunRecorder(max_runs=1)
    summary = recorder.record(run, correlation_id="corr-1", cached=False)
    serialized = json.dumps(summary.as_dict())

    assert marker not in serialized
    assert len(summary.question_hash) == 64
    assert summary.tool_names == ("search_policy",)
    assert summary.evidence_ids == ("evidence-1",)
    assert recorder.latest() == summary
