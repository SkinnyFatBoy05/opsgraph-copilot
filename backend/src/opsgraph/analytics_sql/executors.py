"""Read-only SQLite and PostgreSQL query execution with hard resource bounds."""

import asyncio
import json
import sqlite3
from pathlib import Path
from time import monotonic, perf_counter

import psycopg

from opsgraph.analytics_sql.contracts import SemanticSchema, SqlQueryResult
from opsgraph.analytics_sql.guard import validate_readonly_sql
from opsgraph.observability.tracing import traced


class ReadOnlySqlExecutor:
    def __init__(
        self,
        *,
        schema: SemanticSchema,
        sqlite_path: Path | None = None,
        postgres_url: str | None = None,
        timeout_seconds: float = 3.0,
        max_result_bytes: int = 256_000,
    ) -> None:
        if (sqlite_path is None) == (postgres_url is None):
            raise ValueError("configure exactly one of sqlite_path or postgres_url")
        self.schema = schema
        self.sqlite_path = sqlite_path
        self.postgres_url = postgres_url
        self.timeout_seconds = timeout_seconds
        self.max_result_bytes = max_result_bytes

    async def execute(self, sql: str) -> SqlQueryResult:
        dialect = "sqlite" if self.sqlite_path is not None else "postgres"
        with traced("opsgraph.sql.execute", {"dialect": dialect}):
            if self.sqlite_path is not None:
                validation = validate_readonly_sql(sql, self.schema, "sqlite")
                return await asyncio.to_thread(self._execute_sqlite, validation)
            validation = validate_readonly_sql(sql, self.schema, "postgres")
            return await self._execute_postgres(validation)

    def _execute_sqlite(self, validation) -> SqlQueryResult:
        assert self.sqlite_path is not None
        started = perf_counter()
        deadline = monotonic() + self.timeout_seconds
        uri = f"{self.sqlite_path.resolve().as_uri()}?mode=ro"
        with sqlite3.connect(uri, uri=True, timeout=self.timeout_seconds) as connection:
            connection.execute("PRAGMA query_only = ON")
            connection.set_progress_handler(lambda: 1 if monotonic() > deadline else 0, 1_000)
            cursor = connection.execute(validation.normalized_sql)
            columns = tuple(column[0] for column in cursor.description or ())
            rows, truncated = self._bounded_rows(cursor.fetchall())

        return SqlQueryResult(
            normalized_sql=validation.normalized_sql,
            columns=columns,
            rows=rows,
            row_count=len(rows),
            referenced_tables=validation.referenced_tables,
            elapsed_ms=(perf_counter() - started) * 1000,
            truncated=truncated,
        )

    async def _execute_postgres(self, validation) -> SqlQueryResult:
        assert self.postgres_url is not None
        started = perf_counter()
        async with await psycopg.AsyncConnection.connect(self.postgres_url) as connection:
            async with connection.transaction():
                async with connection.cursor() as cursor:
                    await cursor.execute("SET TRANSACTION READ ONLY")
                    await cursor.execute(
                        f"SET LOCAL statement_timeout = {int(self.timeout_seconds * 1000)}"
                    )
                    await cursor.execute(validation.normalized_sql)
                    columns = tuple(column.name for column in cursor.description or ())
                    fetched = await cursor.fetchall()
        rows, truncated = self._bounded_rows(fetched)
        return SqlQueryResult(
            normalized_sql=validation.normalized_sql,
            columns=columns,
            rows=rows,
            row_count=len(rows),
            referenced_tables=validation.referenced_tables,
            elapsed_ms=(perf_counter() - started) * 1000,
            truncated=truncated,
        )

    def _bounded_rows(self, fetched) -> tuple[tuple[tuple[object, ...], ...], bool]:
        accepted: list[tuple[object, ...]] = []
        serialized_bytes = 0
        for row in fetched:
            normalized = tuple(row)
            row_bytes = len(json.dumps(normalized, default=str).encode("utf-8"))
            if serialized_bytes + row_bytes > self.max_result_bytes:
                return tuple(accepted), True
            accepted.append(normalized)
            serialized_bytes += row_bytes
        return tuple(accepted), False
