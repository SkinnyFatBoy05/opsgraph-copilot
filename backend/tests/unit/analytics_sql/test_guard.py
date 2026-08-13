import pytest

from opsgraph.analytics_sql.guard import SqlRejected, validate_readonly_sql
from opsgraph.analytics_sql.schemas import BANKOPS_SEMANTIC_SCHEMA


@pytest.mark.parametrize(
    "sql",
    [
        "DELETE FROM customers",
        "SELECT 1; DROP TABLE customers",
        "PRAGMA database_list",
        "SELECT * FROM sqlite_master",
        "WITH changed AS (UPDATE accounts SET status='closed' RETURNING *) SELECT * FROM changed",
        "SELECT load_extension('malware')",
        "SELECT * FROM customers -- hide the rest",
    ],
)
def test_rejects_unsafe_sql(sql: str) -> None:
    with pytest.raises(SqlRejected):
        validate_readonly_sql(sql, BANKOPS_SEMANTIC_SCHEMA, "sqlite")


def test_adds_bounded_limit() -> None:
    result = validate_readonly_sql(
        "SELECT case_id FROM service_cases",
        BANKOPS_SEMANTIC_SCHEMA,
        "sqlite",
    )

    assert result.row_limit == 200
    assert "LIMIT 200" in result.normalized_sql.upper()
    assert result.referenced_tables == ("service_cases",)


def test_caps_excessive_limit() -> None:
    result = validate_readonly_sql(
        "SELECT case_id FROM service_cases LIMIT 5000",
        BANKOPS_SEMANTIC_SCHEMA,
        "sqlite",
    )

    assert result.row_limit == 200
    assert "LIMIT 200" in result.normalized_sql.upper()


def test_preserves_smaller_limit() -> None:
    result = validate_readonly_sql(
        "SELECT case_id FROM service_cases LIMIT 10",
        BANKOPS_SEMANTIC_SCHEMA,
        "sqlite",
    )

    assert result.row_limit == 10


def test_accepts_read_only_cte_with_known_columns() -> None:
    result = validate_readonly_sql(
        """
        WITH open_cases AS (
            SELECT case_id, priority FROM service_cases WHERE status = 'open'
        )
        SELECT priority, COUNT(*) AS case_count
        FROM open_cases
        GROUP BY priority
        """,
        BANKOPS_SEMANTIC_SCHEMA,
        "sqlite",
    )

    assert result.referenced_tables == ("service_cases",)


def test_rejects_unknown_table_and_column() -> None:
    with pytest.raises(SqlRejected, match="unknown table"):
        validate_readonly_sql("SELECT * FROM secrets", BANKOPS_SEMANTIC_SCHEMA, "sqlite")
    with pytest.raises(SqlRejected, match="unknown column"):
        validate_readonly_sql(
            "SELECT password_hash FROM customers",
            BANKOPS_SEMANTIC_SCHEMA,
            "sqlite",
        )
