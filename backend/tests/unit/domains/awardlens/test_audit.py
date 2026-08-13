from datetime import date, time
from pathlib import Path

from opsgraph.domains.awardlens.audit import run_audit
from opsgraph.domains.awardlens.models import PayrollRecord
from opsgraph.domains.awardlens.rules import load_rule_set


PROJECT_ROOT = Path(__file__).resolve().parents[5]


def test_audit_totals_only_supported_underpayments() -> None:
    rules = load_rule_set(
        PROJECT_ROOT / "data" / "awardlens" / "rules" / "retail-level-1-2026.json",
        PROJECT_ROOT / "data" / "awardlens" / "rules" / "source-manifest.json",
    )
    records = (
        PayrollRecord(
            record_id="SHIFT-001",
            employee_id="SYN-001",
            shift_date=date(2026, 7, 6),
            start_time=time(9),
            end_time=time(17),
            break_minutes=0,
            classification="retail_level_1",
            employment_type="full_time",
            paid_gross_cents=20_000,
            is_public_holiday=False,
        ),
        PayrollRecord(
            record_id="SHIFT-002",
            employee_id="SYN-002",
            shift_date=date(2026, 7, 6),
            start_time=time(9),
            end_time=time(17),
            break_minutes=0,
            classification="retail_level_2",
            employment_type="full_time",
            paid_gross_cents=0,
            is_public_holiday=False,
        ),
    )

    audit = run_audit(records, rules)

    assert audit.calculated_count == 1
    assert audit.manual_review_count == 1
    assert audit.total_liability_cents == 2_248
    assert audit.findings[1].liability_cents is None
    assert len(audit.input_sha256) == 64
