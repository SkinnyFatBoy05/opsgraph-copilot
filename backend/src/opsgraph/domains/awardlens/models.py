"""Immutable AwardLens payroll, rules, calculation, and audit models."""

from datetime import date, datetime, time
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class Money(BaseModel):
    model_config = ConfigDict(frozen=True)

    cents: int = Field(ge=0)

    @classmethod
    def from_cents(cls, cents: int) -> "Money":
        return cls(cents=cents)


class PayrollRecord(BaseModel):
    model_config = ConfigDict(frozen=True, str_strip_whitespace=True)

    record_id: str = Field(min_length=1, max_length=64)
    employee_id: str = Field(min_length=1, max_length=64)
    shift_date: date
    start_time: time
    end_time: time
    break_minutes: int = Field(ge=0, le=240)
    classification: str = Field(min_length=1, max_length=64)
    employment_type: str = Field(min_length=1, max_length=32)
    paid_gross_cents: int = Field(ge=0, le=10_000_000)
    is_public_holiday: bool = False

    @field_validator("record_id", "employee_id", "classification", "employment_type")
    @classmethod
    def safe_text(cls, value: str) -> str:
        if value[:1] in {"=", "+", "-", "@"}:
            raise ValueError("formula-like values are not permitted")
        return value


class AwardRuleSet(BaseModel):
    model_config = ConfigDict(frozen=True)

    rule_id: str
    award_code: str
    version: str
    effective_from: date
    effective_to: date | None = None
    verification_status: Literal["verified_official", "fictional_demo"]
    supported_classifications: tuple[str, ...]
    supported_employment_types: tuple[str, ...]
    supported_day_types: tuple[str, ...]
    base_rate_cents: dict[str, int]
    multipliers: dict[str, dict[str, Decimal]]
    source_ids: tuple[str, ...]
    exclusions: tuple[str, ...] = ()


class CalculationLine(BaseModel):
    model_config = ConfigDict(frozen=True)

    description: str
    day_type: str
    minutes: int = Field(gt=0)
    base_rate_cents: int = Field(gt=0)
    multiplier: str
    amount_cents: int = Field(ge=0)


class AuditFinding(BaseModel):
    model_config = ConfigDict(frozen=True)

    record_id: str
    employee_id: str
    status: Literal["calculated", "manual_review"]
    calculation_lines: tuple[CalculationLine, ...] = ()
    expected_gross_cents: int | None = Field(default=None, ge=0)
    paid_gross_cents: int = Field(ge=0)
    variance_cents: int | None = None
    liability_cents: int | None = Field(default=None, ge=0)
    reasons: tuple[str, ...] = ()
    rule_version: str
    source_ids: tuple[str, ...]


class AuditRun(BaseModel):
    model_config = ConfigDict(frozen=True)

    audit_id: str
    created_at: datetime
    rule_version: str
    verification_status: Literal["verified_official", "fictional_demo"]
    source_ids: tuple[str, ...]
    record_count: int = Field(ge=0)
    calculated_count: int = Field(ge=0)
    manual_review_count: int = Field(ge=0)
    total_expected_gross_cents: int = Field(ge=0)
    total_paid_gross_cents: int = Field(ge=0)
    total_liability_cents: int = Field(ge=0)
    input_sha256: str = Field(min_length=64, max_length=64)
    findings: tuple[AuditFinding, ...]
    limitations: tuple[str, ...]
