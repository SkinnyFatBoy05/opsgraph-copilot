import pytest

from opsgraph.orchestration.budget import ExecutionBudget, GraphBudgetExceeded


def test_tool_budget_allows_six_calls_and_rejects_the_seventh() -> None:
    budget = ExecutionBudget(max_tool_calls=6)

    assert budget.reserve_tool_calls(current=0, requested=6) == 6
    with pytest.raises(GraphBudgetExceeded) as error:
        budget.reserve_tool_calls(current=6, requested=1)

    assert error.value.code == "GRAPH_BUDGET_EXCEEDED"


def test_retry_budgets_are_explicit() -> None:
    budget = ExecutionBudget(max_sql_repairs=1, max_retrieval_expansions=1)

    budget.ensure_sql_repair_allowed(current=0)
    budget.ensure_retrieval_expansion_allowed(current=0)
    with pytest.raises(GraphBudgetExceeded):
        budget.ensure_sql_repair_allowed(current=1)
    with pytest.raises(GraphBudgetExceeded):
        budget.ensure_retrieval_expansion_allowed(current=1)
