import pytest

from opsgraph.contracts.evidence import EvidenceRef
from opsgraph.contracts.runs import SynthesisRequest
from opsgraph.contracts.tools import AgentTask, ToolDefinition, ToolResult
from opsgraph.providers.fake import DeterministicFakeModel


@pytest.mark.parametrize(
    ("question", "route"),
    [
        ("What does the policy require?", "rag"),
        ("How many cases are overdue?", "sql"),
        ("Which cases are late and what policy applies?", "hybrid"),
        ("Calculate the gross pay for this shift", "calculator"),
        ("Write me a poem", "unsupported"),
    ],
)
async def test_fake_model_routes_deterministically(
    question: str, route: str
) -> None:
    decision = await DeterministicFakeModel().route(question, "bankops")

    assert decision.route == route
    assert decision.reason


async def test_fake_model_only_selects_allowed_tools() -> None:
    model = DeterministicFakeModel()
    task = AgentTask(
        agent="policy_research",
        domain="bankops",
        question="What does the complaint policy require?",
    )
    tools = (
        ToolDefinition(
            name="search_policy",
            description="Search synthetic policy documents",
            input_schema={"type": "object"},
            allowed_domains=("bankops",),
        ),
        ToolDefinition(
            name="award_calculator",
            description="Calculate an Australian award result",
            input_schema={"type": "object"},
            allowed_domains=("awardlens",),
        ),
    )

    calls = await model.choose_tools(task, tools)

    assert [call.name for call in calls] == ["search_policy"]
    assert calls[0].arguments == {"query": task.question}


async def test_fake_model_synthesizes_cited_evidence() -> None:
    evidence = EvidenceRef(
        id="bankops:complaints:v1#sla",
        domain="bankops",
        title="Complaint SLA",
        text="Priority complaints must be acknowledged within four business hours.",
    )

    answer = await DeterministicFakeModel().synthesize(
        SynthesisRequest(
            question="What is the complaint SLA?",
            domain="bankops",
            evidence=(evidence,),
        )
    )

    assert "four business hours" in answer.text
    assert answer.citation_ids == (evidence.id,)


async def test_fake_model_summarizes_sql_without_dumping_raw_rows() -> None:
    sql_evidence = EvidenceRef(
        id="sql-result",
        domain="bankops",
        kind="sql",
        text='{"columns":["case_id"],"rows":[["CASE-0001"]]}',
    )
    policy_evidence = EvidenceRef(
        id="policy-result",
        domain="bankops",
        text="Priority complaints must be acknowledged within four business hours.",
    )
    tool_result = ToolResult(
        call_id="call-1",
        name="query_cases",
        status="succeeded",
        data={
            "columns": ("case_id",),
            "rows": (("CASE-0001",),),
            "row_count": 1,
            "normalized_sql": "SELECT case_id FROM service_cases LIMIT 200",
        },
        evidence=(sql_evidence,),
    )

    answer = await DeterministicFakeModel().synthesize(
        SynthesisRequest(
            question="Which cases are late and what policy applies?",
            domain="bankops",
            evidence=(sql_evidence, policy_evidence),
            tool_results=(tool_result,),
        )
    )

    assert "1 overdue open case" in answer.text
    assert "four business hours" in answer.text
    assert "CASE-0001" not in answer.text
    assert len(answer.text) < 600
