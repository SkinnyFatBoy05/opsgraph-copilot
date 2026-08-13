import sqlite3

import pytest

from opsgraph.analytics_sql.executors import ReadOnlySqlExecutor
from opsgraph.analytics_sql.guard import SqlRejected
from opsgraph.analytics_sql.schemas import BANKOPS_SEMANTIC_SCHEMA
from opsgraph.domains.bankops.seed import seed_bankops


@pytest.fixture
def demo_database(tmp_path):
    path = tmp_path / "bankops.sqlite"
    with sqlite3.connect(path) as connection:
        seed_bankops(connection)
    return path


async def test_readonly_executor_returns_bounded_structured_rows(demo_database) -> None:
    executor = ReadOnlySqlExecutor(
        schema=BANKOPS_SEMANTIC_SCHEMA,
        sqlite_path=demo_database,
    )

    result = await executor.execute(
        """
        SELECT case_id, priority, due_at
        FROM service_cases
        WHERE status = 'open'
        ORDER BY due_at
        """
    )

    assert result.columns == ("case_id", "priority", "due_at")
    assert 0 < result.row_count <= 200
    assert result.normalized_sql.endswith("LIMIT 200")


async def test_readonly_executor_cannot_modify_database(demo_database) -> None:
    executor = ReadOnlySqlExecutor(
        schema=BANKOPS_SEMANTIC_SCHEMA,
        sqlite_path=demo_database,
    )

    with pytest.raises(SqlRejected):
        await executor.execute("UPDATE service_cases SET status = 'closed'")

    with sqlite3.connect(demo_database) as connection:
        open_count = connection.execute(
            "SELECT COUNT(*) FROM service_cases WHERE status = 'open'"
        ).fetchone()[0]
    assert open_count > 0
