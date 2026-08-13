"""AST-level validation for model-generated read-only SQL."""

from typing import Literal

import sqlglot
from sqlglot import exp
from sqlglot.errors import ParseError

from opsgraph.analytics_sql.contracts import SemanticSchema, SqlDialect, SqlValidation
from opsgraph.contracts.errors import ErrorCode, OpsGraphError
from opsgraph.observability.tracing import traced

MAX_SQL_CHARS = 20_000
MAX_ROWS = 200
COMMENT_MARKERS = ("--", "/*", "*/")
BLOCKED_FUNCTIONS = {
    "dblink",
    "fts3_tokenizer",
    "load_extension",
    "pg_ls_dir",
    "pg_read_file",
    "readfile",
    "set_config",
    "writefile",
}
BLOCKED_EXPRESSION_NAMES = (
    "Alter",
    "Attach",
    "Command",
    "Commit",
    "Copy",
    "Create",
    "Delete",
    "Detach",
    "Drop",
    "Insert",
    "Merge",
    "Pragma",
    "Rollback",
    "Transaction",
    "Update",
    "Use",
)
BLOCKED_EXPRESSIONS = tuple(
    expression_type
    for name in BLOCKED_EXPRESSION_NAMES
    if (expression_type := getattr(exp, name, None)) is not None
)


class SqlRejected(OpsGraphError):
    def __init__(self, message: str) -> None:
        super().__init__(ErrorCode.TOOL_REJECTED, message, status_code=422)


def validate_readonly_sql(
    sql: str,
    schema: SemanticSchema,
    dialect: SqlDialect,
) -> SqlValidation:
    with traced(
        "opsgraph.sql.validate",
        {"dialect": dialect, "sql_length": len(sql)},
    ):
        return _validate_readonly_sql(sql, schema, dialect)


def _validate_readonly_sql(
    sql: str,
    schema: SemanticSchema,
    dialect: SqlDialect,
) -> SqlValidation:
    candidate = sql.strip()
    if not candidate:
        raise SqlRejected("SQL must not be empty")
    if len(candidate) > MAX_SQL_CHARS:
        raise SqlRejected(f"SQL exceeds {MAX_SQL_CHARS} characters")
    if any(marker in candidate for marker in COMMENT_MARKERS):
        raise SqlRejected("SQL comments are not permitted")

    try:
        statements = sqlglot.parse(candidate, read=dialect)
    except ParseError as error:
        raise SqlRejected("SQL could not be parsed") from error
    if len(statements) != 1:
        raise SqlRejected("exactly one SQL statement is required")

    statement = statements[0]
    if not isinstance(statement, exp.Query):
        raise SqlRejected("only SELECT queries are permitted")
    if any(statement.find_all(BLOCKED_EXPRESSIONS)):
        raise SqlRejected("mutating or administrative SQL is not permitted")

    with_expression = statement.args.get("with_")
    if with_expression is not None and with_expression.args.get("recursive"):
        raise SqlRejected("recursive CTEs are not permitted")

    cte_names = {
        cte.alias_or_name.casefold()
        for cte in statement.find_all(exp.CTE)
        if cte.alias_or_name
    }
    referenced_tables: set[str] = set()
    for table in statement.find_all(exp.Table):
        table_name = table.name.casefold()
        if table_name in cte_names:
            continue
        if table.catalog or table.db:
            raise SqlRejected("qualified or cross-database tables are not permitted")
        if table_name not in schema.tables:
            raise SqlRejected(f"unknown table: {table_name}")
        referenced_tables.add(table_name)

    _validate_functions(statement)
    _validate_columns(statement, schema, cte_names)
    row_limit = _literal_limit(statement)
    if row_limit is None or row_limit > MAX_ROWS:
        row_limit = MAX_ROWS
        statement = statement.limit(MAX_ROWS, copy=True)

    return SqlValidation(
        normalized_sql=statement.sql(dialect=dialect, pretty=False),
        dialect=dialect,
        row_limit=row_limit,
        referenced_tables=tuple(sorted(referenced_tables)),
    )


def _validate_functions(statement: exp.Expression) -> None:
    for function in statement.find_all(exp.Func):
        names = {
            str(getattr(function, "name", "")).casefold(),
            function.sql_name().casefold(),
        }
        if names & BLOCKED_FUNCTIONS:
            raise SqlRejected(f"function is not permitted: {sorted(names & BLOCKED_FUNCTIONS)[0]}")


def _validate_columns(
    statement: exp.Expression,
    schema: SemanticSchema,
    cte_names: set[str],
) -> None:
    cte_columns = {
        alias.casefold()
        for cte in statement.find_all(exp.CTE)
        for expression in cte.this.expressions
        if (alias := expression.alias_or_name)
    }
    allowed_columns = schema.columns | frozenset(cte_columns) | frozenset(cte_names)
    for column in statement.find_all(exp.Column):
        if column.is_star:
            continue
        name = column.name.casefold()
        if name not in allowed_columns:
            raise SqlRejected(f"unknown column: {name}")


def _literal_limit(statement: exp.Expression) -> int | None:
    limit = statement.args.get("limit")
    if limit is None:
        return None
    expression = limit.expression
    if not isinstance(expression, exp.Literal) or expression.is_string:
        raise SqlRejected("LIMIT must be a positive integer literal")
    try:
        value = int(expression.this)
    except (TypeError, ValueError) as error:
        raise SqlRejected("LIMIT must be a positive integer literal") from error
    if value < 1:
        raise SqlRejected("LIMIT must be positive")
    return value
