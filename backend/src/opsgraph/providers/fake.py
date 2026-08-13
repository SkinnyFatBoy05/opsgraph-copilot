"""A no-cost deterministic model for local development and CI."""

from hashlib import sha256
import re

from opsgraph.contracts.evidence import DomainName
from opsgraph.contracts.runs import DraftAnswer, RouteDecision, SynthesisRequest
from opsgraph.contracts.tools import AgentTask, ToolCall, ToolDefinition


class DeterministicFakeModel:
    """Imitates structured model decisions without network calls or randomness."""

    provider_name = "fake"
    model_name = "deterministic-v1"

    async def route(self, question: str, domain: DomainName) -> RouteDecision:
        normalized = question.casefold()
        policy_terms = ("policy", "require", "rule", "sla", "entitled")
        data_terms = ("how many", "count", "which cases", "overdue", "late")
        calculation_terms = ("calculate", "gross pay", "penalty", "allowance")

        has_policy = any(self._contains_term(normalized, term) for term in policy_terms)
        has_data = any(self._contains_term(normalized, term) for term in data_terms)

        if has_policy and has_data:
            return RouteDecision(
                route="hybrid",
                reason="The question combines operational records with policy evidence.",
            )
        if has_data:
            return RouteDecision(
                route="sql",
                reason="The question asks for facts held in structured records.",
            )
        if has_policy:
            return RouteDecision(
                route="rag",
                reason="The question asks for documentary policy evidence.",
            )
        if any(self._contains_term(normalized, term) for term in calculation_terms):
            return RouteDecision(
                route="calculator",
                reason=f"The {domain} question requires a deterministic calculation.",
            )
        return RouteDecision(
            route="unsupported",
            reason="The question does not match an available evidence workflow.",
        )

    async def choose_tools(
        self,
        task: AgentTask,
        tools: tuple[ToolDefinition, ...],
    ) -> tuple[ToolCall, ...]:
        preferred_names = {
            "policy_research": ("search_policy",),
            "data_analyst": (
                "query_award_findings" if task.domain == "awardlens" else "query_cases",
            ),
            "domain_calculation": (
                "award_calculator" if task.domain == "awardlens" else "calculate_bankops_metrics",
            ),
            "evidence_verifier": ("verify_evidence",),
            "supervisor": (),
        }[task.agent]
        selected = [
            tool
            for tool in tools
            if task.domain in tool.allowed_domains and tool.name in preferred_names
        ]

        return tuple(
            ToolCall(
                id=self._call_id(task, tool.name, index),
                name=tool.name,
                arguments={"query": task.question},
            )
            for index, tool in enumerate(selected)
        )

    async def synthesize(self, request: SynthesisRequest) -> DraftAnswer:
        if not request.evidence:
            return DraftAnswer(
                text="I could not find evidence to answer this question.",
                limitations=("No supporting evidence was returned by the tools.",),
            )

        citation_ids = tuple(item.id for item in request.evidence)
        answer_parts: list[str] = []
        numeric_facts: dict[str, int | float | str] = {}

        sql_result = next(
            (
                result
                for result in request.tool_results
                if result.name in {"query_cases", "query_award_findings"}
            ),
            None,
        )
        if sql_result is not None:
            columns = tuple(sql_result.data.get("columns", ()))
            rows = tuple(sql_result.data.get("rows", ()))
            if request.domain == "awardlens":
                finding_count = int(sql_result.data.get("numeric_facts", {}).get("finding_count", len(rows)))
                noun = "finding" if finding_count == 1 else "findings"
                answer_parts.append(
                    f"The guarded read-only query returned {finding_count} synthetic audit {noun}."
                )
                numeric_facts["finding_count"] = finding_count
            else:
                if columns and columns[0] == "overdue_count" and rows:
                    overdue_count = int(rows[0][0])
                else:
                    overdue_count = int(sql_result.data.get("row_count", len(rows)))
                noun = "case" if overdue_count == 1 else "cases"
                answer_parts.append(
                    f"The read-only query identified {overdue_count} overdue open {noun} "
                    "in the synthetic dataset."
                )
                numeric_facts["overdue_open_cases"] = overdue_count

        calculation = next(
            (
                result
                for result in request.tool_results
                if result.name in {"calculate_bankops_metrics", "award_calculator"}
            ),
            None,
        )
        if calculation is not None:
            supported_facts = dict(calculation.data.get("numeric_facts", {}))
            if supported_facts:
                numeric_facts.update(supported_facts)
                formatted = ", ".join(f"{key}={value}" for key, value in supported_facts.items())
                answer_parts.append(f"The deterministic calculator returned: {formatted}.")
            else:
                count = len(calculation.data.get("calculations", ()))
                answer_parts.append(
                    f"The deterministic calculator returned {count} supported result"
                    f"{'s' if count != 1 else ''}."
                )

        document_evidence = [item for item in request.evidence if item.kind == "document"]
        if document_evidence:
            normalized_question = request.question.casefold()
            preferred = next(
                (
                    item
                    for item in document_evidence
                    if "complaint" in normalized_question
                    and "complaint" in f"{item.title} {item.section}".casefold()
                ),
                document_evidence[0],
            )
            answer_parts.append(f"The retrieved synthetic policy states: {_excerpt(preferred.text)}")

        if not answer_parts:
            non_sql = next(
                (item for item in request.evidence if item.kind != "sql"),
                request.evidence[0],
            )
            answer_parts.append(_excerpt(non_sql.text))

        return DraftAnswer(
            text=" ".join(answer_parts),
            citation_ids=citation_ids,
            numeric_facts=numeric_facts,
        )

    @staticmethod
    def _call_id(task: AgentTask, tool_name: str, index: int) -> str:
        material = f"{task.domain}:{task.agent}:{tool_name}:{task.question}:{index}"
        return f"call-{sha256(material.encode()).hexdigest()[:12]}"

    @staticmethod
    def _contains_term(text: str, term: str) -> bool:
        return re.search(rf"\b{re.escape(term)}\b", text) is not None


def _excerpt(text: str, max_characters: int = 320) -> str:
    normalized = " ".join(text.split())
    if len(normalized) <= max_characters:
        return normalized
    boundary = normalized.rfind(".", 0, max_characters)
    if boundary >= 80:
        return normalized[: boundary + 1]
    return f"{normalized[: max_characters - 1].rstrip()}…"
