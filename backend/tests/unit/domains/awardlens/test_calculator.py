from datetime import date, time
from pathlib import Path

from opsgraph.domains.awardlens.calculator import calculate_shift
from opsgraph.domains.awardlens.models import PayrollRecord
from opsgraph.domains.awardlens.rules import load_rule_set


PROJECT_ROOT = Path(__file__).resolve().parents[5]


def rule_set():
    return load_rule_set(
        PROJECT_ROOT / "data" / "awardlens" / "rules" / "retail-level-1-2026.json",
        PROJECT_ROOT / "data" / "awardlens" / "rules" / "source-manifest.json",
    )


def record(**overrides) -> PayrollRecord:
    values = {
        "record_id": "SHIFT-001",
        "employee_id": "SYN-001",
        "shift_date": date(2026, 7, 6),
        "start_time": time(9, 0),
        "end_time": time(17, 0),
        "break_minutes": 0,
        "classification": "retail_level_1",
        "employment_type": "full_time",
        "paid_gross_cents": 0,
        "is_public_holiday": False,
    }
    values.update(overrides)
    return PayrollRecord(**values)


def test_public_holiday_precedes_sunday() -> None:
    finding = calculate_shift(
        record(shift_date=date(2026, 7, 5), is_public_holiday=True),
        rule_set(),
    )

    assert finding.calculation_lines[0].day_type == "public_holiday"
    assert finding.expected_gross_cents == 50_058


def test_unsupported_classification_has_no_liability() -> None:
    finding = calculate_shift(record(classification="retail_level_2"), rule_set())

    assert finding.status == "manual_review"
    assert finding.expected_gross_cents is None
    assert finding.liability_cents is None


def test_calculation_uses_integer_cents_and_round_half_up() -> None:
    finding = calculate_shift(
        record(
            shift_date=date(2026, 7, 4),
            start_time=time(9, 0),
            end_time=time(14, 0),
        ),
        rule_set(),
    )

    assert finding.expected_gross_cents == 17_381
    assert finding.calculation_lines[0].multiplier == "1.25"


def test_casual_saturday_rate_includes_casual_loading() -> None:
    finding = calculate_shift(
        record(
            shift_date=date(2026, 7, 4),
            start_time=time(9, 0),
            end_time=time(14, 0),
            employment_type="casual",
        ),
        rule_set(),
    )

    assert finding.status == "calculated"
    assert finding.expected_gross_cents == 20_858
    assert finding.calculation_lines[0].multiplier == "1.50"


def test_shift_crossing_evening_boundary_requires_manual_review() -> None:
    finding = calculate_shift(
        record(start_time=time(17, 0), end_time=time(20, 0)),
        rule_set(),
    )

    assert finding.status == "manual_review"
    assert "multiplier boundary" in finding.reasons[0]
