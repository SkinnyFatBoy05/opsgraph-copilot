"""Deterministic operations metrics used by BankOps tools and evaluations."""

from datetime import datetime, time, timedelta
from decimal import Decimal

BUSINESS_DAY_START = time(9, 0)
BUSINESS_DAY_END = time(17, 0)


def business_hours_between(start: datetime, end: datetime) -> Decimal:
    """Return weekday hours within 09:00-17:00 in the start timezone.

    Public holidays are deliberately excluded from this synthetic demo rule.
    """

    if start.tzinfo is None or start.utcoffset() is None:
        raise ValueError("start and end must be timezone-aware datetimes")
    if end.tzinfo is None or end.utcoffset() is None:
        raise ValueError("start and end must be timezone-aware datetimes")
    if end < start:
        raise ValueError("end must not be earlier than start")

    local_end = end.astimezone(start.tzinfo)
    current_date = start.date()
    total_seconds = Decimal(0)

    while current_date <= local_end.date():
        if current_date.weekday() < 5:
            day_start = datetime.combine(current_date, BUSINESS_DAY_START, start.tzinfo)
            day_end = datetime.combine(current_date, BUSINESS_DAY_END, start.tzinfo)
            overlap_start = max(start, day_start)
            overlap_end = min(local_end, day_end)
            if overlap_end > overlap_start:
                total_seconds += Decimal(str((overlap_end - overlap_start).total_seconds()))
        current_date += timedelta(days=1)

    return total_seconds / Decimal(3600)
