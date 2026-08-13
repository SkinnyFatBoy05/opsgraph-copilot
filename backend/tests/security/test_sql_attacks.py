import pytest

from opsgraph.analytics_sql.guard import SqlRejected, validate_readonly_sql
from opsgraph.analytics_sql.schemas import BANKOPS_SEMANTIC_SCHEMA


@pytest.mark.parametrize(
    "payload",
    [
        "ATTACH DATABASE 'stolen.db' AS stolen",
        "DETACH DATABASE main",
        "VACUUM",
        "SELECT readfile('C:/Windows/win.ini')",
        "SELECT writefile('payload.txt', 'owned')",
        "SELECT * FROM pragma_table_info('customers')",
        "SELECT sql FROM sqlite_schema",
        "WITH RECURSIVE bomb(x) AS (SELECT 1 UNION ALL SELECT x + 1 FROM bomb) SELECT * FROM bomb",
        "SELECT * FROM customers /* comment */",
    ],
)
def test_known_sql_attack_payloads_are_rejected(payload: str) -> None:
    with pytest.raises(SqlRejected):
        validate_readonly_sql(payload, BANKOPS_SEMANTIC_SCHEMA, "sqlite")
