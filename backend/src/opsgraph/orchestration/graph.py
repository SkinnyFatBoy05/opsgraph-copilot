"""LangGraph topology for bounded supervisor/specialist orchestration."""

from dataclasses import dataclass, field

from langgraph.graph import END, START, StateGraph

from opsgraph.orchestration.budget import ExecutionBudget
from opsgraph.orchestration.nodes import GraphNodes, NodeDependencies
from opsgraph.orchestration.state import OpsGraphState
from opsgraph.providers.base import AgentModel
from opsgraph.tools.registry import ToolRegistry


@dataclass(frozen=True)
class GraphDependencies:
    model: AgentModel
    registry: ToolRegistry
    budget: ExecutionBudget = field(default_factory=ExecutionBudget)


def build_graph(dependencies: GraphDependencies):
    nodes = GraphNodes(
        NodeDependencies(
            model=dependencies.model,
            registry=dependencies.registry,
            budget=dependencies.budget,
        )
    )
    graph = StateGraph(OpsGraphState)
    graph.add_node("input_guard", nodes.input_guard)
    graph.add_node("supervisor", nodes.supervisor)
    graph.add_node("policy_research", nodes.policy_research)
    graph.add_node("data_analyst", nodes.data_analyst)
    graph.add_node("domain_calculation", nodes.domain_calculation)
    graph.add_node("evidence_join", nodes.evidence_join)
    graph.add_node("synthesis", nodes.synthesis)
    graph.add_node("verifier", nodes.verifier)
    graph.add_node("correction", nodes.correction)
    graph.add_node("manual_review", nodes.manual_review)

    graph.add_edge(START, "input_guard")
    graph.add_conditional_edges(
        "input_guard",
        lambda state: "manual_review" if state.get("error_code") else "supervisor",
    )
    graph.add_conditional_edges("supervisor", _route_specialists)
    for specialist in ("policy_research", "data_analyst", "domain_calculation"):
        graph.add_conditional_edges(
            specialist,
            lambda state: "manual_review" if state.get("error_code") else "evidence_join",
        )
    graph.add_edge("evidence_join", "synthesis")
    graph.add_edge("synthesis", "verifier")
    graph.add_conditional_edges("verifier", _after_verification)
    graph.add_edge("correction", "verifier")
    graph.add_edge("manual_review", END)
    return graph.compile()


def _route_specialists(state: OpsGraphState):
    route = state["route"]
    if route == "rag":
        return "policy_research"
    if route == "sql":
        return "data_analyst"
    if route == "hybrid":
        return ["policy_research", "data_analyst"]
    if route == "calculator":
        return "domain_calculation"
    return "manual_review"


def _after_verification(state: OpsGraphState):
    if state.get("status") == "completed":
        return END
    if state.get("correction_count", 0) < 1 and state.get("evidence"):
        return "correction"
    return "manual_review"
