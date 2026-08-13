"""Explicit LangGraph nodes; each node has one bounded responsibility."""

from dataclasses import dataclass

from opsgraph.contracts.runs import DraftAnswer, SynthesisRequest, VerifiedAnswer
from opsgraph.contracts.tools import AgentName, AgentTask
from opsgraph.orchestration.budget import ExecutionBudget, GraphBudgetExceeded
from opsgraph.orchestration.state import OpsGraphState
from opsgraph.observability.tracing import traced
from opsgraph.providers.base import AgentModel
from opsgraph.tools.registry import ToolRegistry


@dataclass(frozen=True)
class NodeDependencies:
    model: AgentModel
    registry: ToolRegistry
    budget: ExecutionBudget


class GraphNodes:
    def __init__(self, dependencies: NodeDependencies) -> None:
        self.dependencies = dependencies

    async def input_guard(self, state: OpsGraphState) -> dict:
        question = state["question"].strip()
        prohibited = ("delete ", "update ", "approve the loan", "accuse", "password")
        if len(question) > 2_000:
            return {
                "error_code": "INVALID_REQUEST",
                "error_message": "Question exceeds 2,000 characters.",
            }
        if any(term in question.casefold() for term in prohibited):
            return {
                "error_code": "UNSUPPORTED_REQUEST",
                "error_message": "The request asks for a prohibited decision or mutation.",
            }
        return {"question": question}

    async def supervisor(self, state: OpsGraphState) -> dict:
        with traced("opsgraph.route", {"domain": state["domain"]}):
            decision = await self.dependencies.model.route(state["question"], state["domain"])
        return {"route": decision.route, "route_reason": decision.reason}

    async def policy_research(self, state: OpsGraphState) -> dict:
        return await self._specialist("policy_research", state)

    async def data_analyst(self, state: OpsGraphState) -> dict:
        return await self._specialist("data_analyst", state)

    async def domain_calculation(self, state: OpsGraphState) -> dict:
        return await self._specialist("domain_calculation", state)

    async def evidence_join(self, state: OpsGraphState) -> dict:
        return {}

    async def synthesis(self, state: OpsGraphState) -> dict:
        with traced(
            "opsgraph.model",
            {
                "operation": "synthesis",
                "provider": self.dependencies.model.provider_name,
                "model": self.dependencies.model.model_name,
            },
        ):
            draft = await self.dependencies.model.synthesize(
                SynthesisRequest(
                    question=state["question"],
                    domain=state["domain"],
                    evidence=state.get("evidence", ()),
                    tool_results=state.get("tool_results", ()),
                )
            )
        return {"draft_answer": draft}

    async def verifier(self, state: OpsGraphState) -> dict:
        with traced(
            "opsgraph.verify",
            {
                "domain": state["domain"],
                "citation_count": len(state["draft_answer"].citation_ids),
            },
        ):
            evidence = state.get("evidence", ())
            draft = state["draft_answer"]
            valid_ids = {item.id for item in evidence if item.domain == state["domain"]}
            citations_valid = bool(draft.citation_ids) and set(draft.citation_ids) <= valid_ids
            deterministic_facts = {
                key: value
                for result in state.get("tool_results", ())
                for key, value in result.data.get("numeric_facts", {}).items()
            }
            numbers_valid = all(
                draft.numeric_facts.get(key) == value
                for key, value in deterministic_facts.items()
            )
        if citations_valid and numbers_valid:
            citations = tuple(item for item in evidence if item.id in draft.citation_ids)
            return {
                "agents": ("evidence_verifier",),
                "answer": VerifiedAnswer(
                    text=draft.text,
                    citations=citations,
                    numeric_facts=draft.numeric_facts,
                    limitations=(
                        *draft.limitations,
                        "Uses fictional policies and synthetic records; human review is required.",
                    ),
                    verified=True,
                ),
                "status": "completed",
            }
        return {
            "agents": ("evidence_verifier",),
            "error_code": "INSUFFICIENT_EVIDENCE",
            "error_message": (
                "The draft changed a deterministic numeric value."
                if citations_valid and not numbers_valid
                else "The draft contained missing or invalid evidence citations."
            ),
        }

    async def correction(self, state: OpsGraphState) -> dict:
        evidence = state.get("evidence", ())
        draft = state["draft_answer"]
        corrected = DraftAnswer(
            text=draft.text,
            citation_ids=tuple(item.id for item in evidence),
            numeric_facts=draft.numeric_facts,
            limitations=draft.limitations,
        )
        return {
            "draft_answer": corrected,
            "correction_count": state.get("correction_count", 0) + 1,
            "error_code": "",
            "error_message": "",
        }

    async def manual_review(self, state: OpsGraphState) -> dict:
        reason = state.get("error_message") or "This request is outside the supported workflow."
        answer = state.get("answer") or VerifiedAnswer(
            text=f"Manual review required. {reason}",
            citations=state.get("evidence", ()),
            limitations=(
                "No automated operational decision was made.",
                "Uses fictional policies and synthetic records.",
            ),
            verified=False,
        )
        return {"answer": answer, "status": "manual_review"}

    async def _specialist(
        self,
        agent: AgentName,
        state: OpsGraphState,
    ) -> dict:
        task = AgentTask(
            agent=agent,
            domain=state["domain"],
            question=state["question"],
            context=state.get("evidence", ()),
        )
        tools = self.dependencies.registry.definitions_for(agent, state["domain"])
        calls = await self.dependencies.model.choose_tools(task, tools)
        try:
            self.dependencies.budget.reserve_tool_calls(
                current=len(state.get("tool_calls", ())),
                requested=len(calls),
            )
        except GraphBudgetExceeded as error:
            return {
                "agents": (agent,),
                "error_code": error.code,
                "error_message": str(error),
            }

        results = tuple(
            [await self.dependencies.registry.invoke(agent, state["domain"], call) for call in calls]
        )
        evidence = tuple(item for result in results for item in result.evidence)
        return {
            "agents": (agent,),
            "tool_calls": calls,
            "tool_results": results,
            "evidence": evidence,
        }
