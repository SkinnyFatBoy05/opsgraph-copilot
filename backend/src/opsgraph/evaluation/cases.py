"""Typed evaluation cases, observed results, and report summaries."""

import json
from decimal import Decimal
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from opsgraph.contracts.evidence import DomainName
from opsgraph.contracts.runs import RouteKind, RunStatus

SqlSafety = Literal["not_applicable", "safe", "rejected"]


class EvaluationCase(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str = Field(min_length=1)
    suite: Literal["bankops", "security", "awardlens"]
    domain: DomainName
    category: str = Field(min_length=1)
    question: str = ""
    input_sql: str | None = None
    expected_route: RouteKind
    expected_status: RunStatus
    expected_min_evidence: int = Field(default=0, ge=0)
    expected_sql_contains: tuple[str, ...] = ()
    expected_numeric_facts: dict[str, int | float | str] = Field(default_factory=dict)
    tags: tuple[str, ...] = ()

    @model_validator(mode="after")
    def has_one_input(self) -> "EvaluationCase":
        if not self.question.strip() and not self.input_sql:
            raise ValueError("an evaluation case requires question or input_sql")
        return self


class EvaluationResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    case_id: str
    domain: DomainName
    category: str
    provider: str
    expected_route: RouteKind
    actual_route: RouteKind
    expected_status: RunStatus
    actual_status: RunStatus
    citation_ids: tuple[str, ...] = ()
    valid_evidence_ids: tuple[str, ...] = ()
    retrieval_hit: bool = True
    sql_safety: SqlSafety = "not_applicable"
    sql_executed: bool = False
    sql_execution_correct: bool = True
    numeric_preserved: bool = True
    abstention_correct: bool = True
    unsupported_liability: bool = False
    secret_leaked: bool = False
    latency_ms: float = Field(ge=0)
    input_tokens: int = Field(default=0, ge=0)
    output_tokens: int = Field(default=0, ge=0)
    estimated_cost_usd: Decimal = Field(default=Decimal("0"), ge=0)
    failures: tuple[str, ...] = ()


class EvaluationSummary(BaseModel):
    model_config = ConfigDict(frozen=True)

    provider: str
    deterministic: bool
    suite_version: str
    generated_at: str
    total_cases: int = Field(ge=0)
    passed_cases: int = Field(ge=0)
    metrics: dict[str, float]
    release_failures: tuple[str, ...]
    estimated_cost_usd: Decimal = Field(ge=0)
    results: tuple[EvaluationResult, ...]


def load_cases(paths: tuple[Path, ...]) -> tuple[EvaluationCase, ...]:
    loaded: list[EvaluationCase] = []
    seen: set[str] = set()
    for path in paths:
        document = json.loads(path.read_text(encoding="utf-8"))
        for raw_case in document["cases"]:
            case = EvaluationCase.model_validate(raw_case)
            if case.id in seen:
                raise ValueError(f"duplicate evaluation case id: {case.id}")
            seen.add(case.id)
            loaded.append(case)
    return tuple(loaded)
