"""Strict CSV ingestion for bounded synthetic payroll uploads."""

import csv
import io

from pydantic import ValidationError

from opsgraph.domains.awardlens.models import PayrollRecord

MAX_CSV_BYTES = 1_000_000
MAX_RECORDS = 500
REQUIRED_COLUMNS = (
    "record_id",
    "employee_id",
    "shift_date",
    "start_time",
    "end_time",
    "break_minutes",
    "classification",
    "employment_type",
    "paid_gross_cents",
    "is_public_holiday",
)


class PayrollCsvError(ValueError):
    """Raised for malformed, unsafe, or out-of-bounds payroll CSV input."""


def parse_payroll_csv(payload: bytes) -> tuple[PayrollRecord, ...]:
    if not payload:
        raise PayrollCsvError("payroll CSV is empty")
    if len(payload) > MAX_CSV_BYTES:
        raise PayrollCsvError(f"payroll CSV exceeds {MAX_CSV_BYTES} bytes")
    try:
        text = payload.decode("utf-8-sig", errors="strict")
    except UnicodeDecodeError as error:
        raise PayrollCsvError("payroll CSV must be UTF-8") from error
    if "\x00" in text:
        raise PayrollCsvError("payroll CSV contains a null byte")

    reader = csv.DictReader(io.StringIO(text, newline=""))
    if tuple(reader.fieldnames or ()) != REQUIRED_COLUMNS:
        raise PayrollCsvError("payroll CSV columns do not match the required schema")

    records: list[PayrollRecord] = []
    seen_ids: set[str] = set()
    for line_number, row in enumerate(reader, start=2):
        if len(records) >= MAX_RECORDS:
            raise PayrollCsvError(f"payroll CSV exceeds {MAX_RECORDS} records")
        if None in row:
            raise PayrollCsvError(f"row {line_number} contains unexpected columns")
        try:
            record = PayrollRecord.model_validate(
                {
                    **row,
                    "break_minutes": int(row["break_minutes"]),
                    "paid_gross_cents": int(row["paid_gross_cents"]),
                    "is_public_holiday": _parse_bool(row["is_public_holiday"]),
                }
            )
        except (KeyError, TypeError, ValueError, ValidationError) as error:
            message = str(error)
            if "formula-like" in message:
                raise PayrollCsvError(f"row {line_number} contains a formula-like value") from error
            raise PayrollCsvError(f"row {line_number} is invalid") from error
        if record.record_id in seen_ids:
            raise PayrollCsvError(f"duplicate record_id: {record.record_id}")
        seen_ids.add(record.record_id)
        records.append(record)
    if not records:
        raise PayrollCsvError("payroll CSV has no records")
    return tuple(records)


def _parse_bool(value: str) -> bool:
    normalized = value.strip().casefold()
    if normalized == "true":
        return True
    if normalized == "false":
        return False
    raise PayrollCsvError("is_public_holiday must be true or false")
