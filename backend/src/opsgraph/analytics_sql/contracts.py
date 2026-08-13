"""Contracts for semantic schemas and bounded query results."""

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

SqlDialect = Literal["sqlite", "postgres"]


class SemanticSchema(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str
    tables: dict[str, tuple[str, ...]]
    descriptions: dict[str, str] = Field(default_factory=dict)

    @property
    def columns(self) -> frozenset[str]:
        return frozenset(column for columns in self.tables.values() for column in columns)


class SqlValidation(BaseModel):
    model_config = ConfigDict(frozen=True)

    normalized_sql: str
    dialect: SqlDialect
    row_limit: int = Field(ge=1, le=200)
    referenced_tables: tuple[str, ...]


class SqlQueryResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    normalized_sql: str
    columns: tuple[str, ...]
    rows: tuple[tuple[Any, ...], ...]
    row_count: int = Field(ge=0, le=200)
    referenced_tables: tuple[str, ...]
    elapsed_ms: float = Field(ge=0)
    truncated: bool = False
