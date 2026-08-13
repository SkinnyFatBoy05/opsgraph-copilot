from datetime import date, time
from pathlib import Path

from opsgraph.domains.awardlens.adapter import AwardLensExplanationService
from opsgraph.domains.awardlens.calculator import calculate_shift
from opsgraph.domains.awardlens.models import PayrollRecord
from opsgraph.domains.awardlens.report import render_audit_report
from opsgraph.domains.awardlens.rules import load_rule_set
from opsgraph.domains.awardlens.audit import run_audit
from opsgraph.providers.fake import DeterministicFakeModel


PROJECT_ROOT = Path(__file__).resolve().parents[3]


def rules():
    return load_rule_set(
        PROJECT_ROOT / "data" / "awardlens" / "rules" / "retail-level-1-2026.json",
        PROJECT_ROOT / "data" / "awardlens" / "rules" / "source-manifest.json",
    )


def payroll_record(**overrides) -> PayrollRecord:
    values = {
        "record_id": "SHIFT-001",
        "employee_id": "SYN-001",
        "shift_date": date(2026, 7, 6),
        "start_time": time(9),
        "end_time": time(17),
        "break_minutes": 0,
        "classification": "retail_level_1",
        "employment_type": "full_time",
        "paid_gross_cents": 20_000,
        "is_public_holiday": False,
    }
    values.update(overrides)
    return PayrollRecord(**values)


async def test_explanation_preserves_calculated_amount() -> None:
    finding = calculate_shift(payroll_record(), rules())
    service = AwardLensExplanationService(DeterministicFakeModel())

    result = await service.explain(finding)

    assert result.numeric_facts["expected_gross_cents"] == 22_248
    assert "22248" in result.text


def test_report_escapes_active_content_and_avoids_legal_conclusions() -> None:
    audit = run_audit((payroll_record(employee_id="<img src=x onerror=alert(1)>"),), rules())

    report = render_audit_report(audit)

    assert "<img" not in report.casefold()
    assert "&lt;img" in report
    assert "<script" not in report.casefold()
    assert "has broken the law" not in report.casefold()


def test_unsupported_record_never_receives_liability() -> None:
    finding = calculate_shift(payroll_record(classification="retail_level_2"), rules())

    assert finding.status == "manual_review"
    assert finding.liability_cents is None
