"""Application-facing service for executing the compiled graph."""

from datetime import UTC, datetime
from uuid import uuid4

from opsgraph.contracts.evidence import DomainName
from opsgraph.contracts.runs import RunResult, RunTrace, VerifiedAnswer
from opsgraph.observability.costs import estimate_cost
from opsgraph.observability.tracing import traced
from opsgraph.orchestration.graph import GraphDependencies, build_graph


class OpsGraphService:
    def __init__(self, dependencies: GraphDependencies) -> None:
        self.dependencies = dependencies
        self.graph = build_graph(dependencies)

    async def run(self, domain: DomainName, question: str) -> RunResult:
        started_at = datetime.now(UTC)
        run_id = f"run-{uuid4().hex}"
        with traced(
            "opsgraph.workflow",
            {"run_id": run_id, "domain": domain, "question": question},
        ):
            state = await self.graph.ainvoke(
                {
                    "run_id": run_id,
                    "domain": domain,
                    "question": question,
                    "started_at": started_at,
                    "status": "running",
                    "agents": (),
                    "evidence": (),
                    "tool_calls": (),
                    "tool_results": (),
                    "correction_count": 0,
                }
            )
        status = state.get("status", "failed")
        answer = state.get("answer") or VerifiedAnswer(
            text="The workflow failed before an answer could be produced.",
            limitations=("No automated decision was made.",),
            verified=False,
        )
        trace = RunTrace(
            run_id=run_id,
            domain=domain,
            question=question,
            route=state.get("route", "unsupported"),
            status=status,
            started_at=started_at,
            completed_at=datetime.now(UTC),
            agents=state.get("agents", ()),
            tool_calls=state.get("tool_calls", ()),
            tool_results=state.get("tool_results", ()),
            provider=self.dependencies.model.provider_name,
            model=self.dependencies.model.model_name,
            estimated_cost_usd=float(
                estimate_cost(
                    self.dependencies.model.provider_name,
                    self.dependencies.model.model_name,
                    0,
                    0,
                )
            ),
        )
        return RunResult(
            answer=answer,
            trace=trace,
            evidence=state.get("evidence", ()),
            tool_results=state.get("tool_results", ()),
            error_code=state.get("error_code") or None,
        )
