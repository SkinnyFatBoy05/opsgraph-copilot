"""Deterministic, bounded AwardLens shift calculation."""

from datetime import datetime, time
from decimal import Decimal, ROUND_HALF_UP

from opsgraph.domains.awardlens.models import (
    AuditFinding,
    AwardRuleSet,
    CalculationLine,
    PayrollRecord,
)
from opsgraph.observability.tracing import traced

EVENING_START = time(18, 0)
MAX_ORDINARY_MINUTES = 10 * 60


def calculate_shift(record: PayrollRecord, rules: AwardRuleSet) -> AuditFinding:
    with traced(
        "opsgraph.calculation",
        {
            "domain": "awardlens",
            "record_id": record.record_id,
            "rule_version": rules.version,
        },
    ):
        reason = _unsupported_reason(record, rules)
        if reason is not None:
            return _manual_review(record, rules, reason)

        start = datetime.combine(record.shift_date, record.start_time)
        end = datetime.combine(record.shift_date, record.end_time)
        payable_minutes = int((end - start).total_seconds() // 60) - record.break_minutes
        if payable_minutes <= 0:
            return _manual_review(record, rules, "Shift has no positive payable duration.")
        if payable_minutes > MAX_ORDINARY_MINUTES:
            return _manual_review(record, rules, "Potential overtime is outside the supported scope.")

        day_type = _day_type(record)
        rate_group = "casual" if record.employment_type == "casual" else "full_time_part_time"
        multiplier = rules.multipliers[rate_group][day_type]
        base_rate = rules.base_rate_cents[record.classification]
        amount = (
            Decimal(base_rate) * multiplier * Decimal(payable_minutes) / Decimal(60)
        ).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
        expected = int(amount)
        variance = expected - record.paid_gross_cents
        line = CalculationLine(
            description=f"{payable_minutes} ordinary minutes at {day_type} rate",
            day_type=day_type,
            minutes=payable_minutes,
            base_rate_cents=base_rate,
            multiplier=str(multiplier),
            amount_cents=expected,
        )
        return AuditFinding(
            record_id=record.record_id,
            employee_id=record.employee_id,
            status="calculated",
            calculation_lines=(line,),
            expected_gross_cents=expected,
            paid_gross_cents=record.paid_gross_cents,
            variance_cents=variance,
            liability_cents=max(variance, 0),
            rule_version=rules.version,
            source_ids=rules.source_ids,
        )


def _unsupported_reason(record: PayrollRecord, rules: AwardRuleSet) -> str | None:
    if record.classification not in rules.supported_classifications:
        return f"Classification {record.classification} is outside the supported scope."
    if record.employment_type not in rules.supported_employment_types:
        return f"Employment type {record.employment_type} is outside the supported scope."
    if record.end_time <= record.start_time:
        return "Overnight or non-positive shifts require manual review."
    if (
        not record.is_public_holiday
        and record.shift_date.weekday() < 5
        and record.start_time < EVENING_START < record.end_time
    ):
        return "Shift crosses a multiplier boundary and requires manual review."
    return None


def _day_type(record: PayrollRecord) -> str:
    if record.is_public_holiday:
        return "public_holiday"
    weekday = record.shift_date.weekday()
    if weekday == 6:
        return "sunday"
    if weekday == 5:
        return "saturday"
    if record.start_time >= EVENING_START:
        return "weekday_evening"
    return "weekday"


def _manual_review(
    record: PayrollRecord,
    rules: AwardRuleSet,
    reason: str,
) -> AuditFinding:
    return AuditFinding(
        record_id=record.record_id,
        employee_id=record.employee_id,
        status="manual_review",
        paid_gross_cents=record.paid_gross_cents,
        reasons=(reason,),
        rule_version=rules.version,
        source_ids=rules.source_ids,
    )
