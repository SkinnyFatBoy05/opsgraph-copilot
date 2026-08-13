from pathlib import Path

import pytest

from opsgraph.domains.awardlens.csv_ingestion import PayrollCsvError, parse_payroll_csv


def test_parses_strict_synthetic_payroll_csv() -> None:
    rows = parse_payroll_csv(
        b"record_id,employee_id,shift_date,start_time,end_time,break_minutes,classification,employment_type,paid_gross_cents,is_public_holiday\n"
        b"SHIFT-001,SYN-001,2026-07-06,09:00,17:00,30,retail_level_1,full_time,20858,false\n"
    )

    assert len(rows) == 1
    assert rows[0].record_id == "SHIFT-001"
    assert rows[0].paid_gross_cents == 20_858
    assert rows[0].is_public_holiday is False


def test_duplicate_record_ids_are_rejected() -> None:
    payload = (
        "record_id,employee_id,shift_date,start_time,end_time,break_minutes,classification,employment_type,paid_gross_cents,is_public_holiday\n"
        "SHIFT-001,SYN-001,2026-07-06,09:00,17:00,30,retail_level_1,full_time,20858,false\n"
        "SHIFT-001,SYN-002,2026-07-07,09:00,17:00,30,retail_level_1,part_time,20858,false\n"
    ).encode()

    with pytest.raises(PayrollCsvError, match="duplicate record_id"):
        parse_payroll_csv(payload)


def test_spreadsheet_formula_values_are_rejected() -> None:
    payload = (
        "record_id,employee_id,shift_date,start_time,end_time,break_minutes,classification,employment_type,paid_gross_cents,is_public_holiday\n"
        "SHIFT-001,=HYPERLINK('bad'),2026-07-06,09:00,17:00,30,retail_level_1,full_time,20858,false\n"
    ).encode()

    with pytest.raises(PayrollCsvError, match="formula-like"):
        parse_payroll_csv(payload)
