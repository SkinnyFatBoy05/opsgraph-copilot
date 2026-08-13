"""Hard graph execution limits."""

from dataclasses import dataclass


class GraphBudgetExceeded(RuntimeError):
    code = "GRAPH_BUDGET_EXCEEDED"


@dataclass(frozen=True)
class ExecutionBudget:
    max_tool_calls: int = 6
    max_sql_repairs: int = 1
    max_retrieval_expansions: int = 1
    max_corrections: int = 1

    def reserve_tool_calls(self, *, current: int, requested: int) -> int:
        proposed = current + requested
        if requested < 0 or proposed > self.max_tool_calls:
            raise GraphBudgetExceeded(
                f"tool-call budget exceeded: {proposed}/{self.max_tool_calls}"
            )
        return proposed

    def ensure_sql_repair_allowed(self, *, current: int) -> None:
        if current >= self.max_sql_repairs:
            raise GraphBudgetExceeded("SQL repair budget exceeded")

    def ensure_retrieval_expansion_allowed(self, *, current: int) -> None:
        if current >= self.max_retrieval_expansions:
            raise GraphBudgetExceeded("retrieval expansion budget exceeded")
