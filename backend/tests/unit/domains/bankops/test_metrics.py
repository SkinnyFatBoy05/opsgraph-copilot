from datetime import UTC, datetime
from decimal import Decimal

from opsgraph.domains.bankops.metrics import business_hours_between


def test_business_hours_between_within_one_workday() -> None:
    start = datetime(2026, 8, 3, 10, 30, tzinfo=UTC)  # Monday
    end = datetime(2026, 8, 3, 15, 45, tzinfo=UTC)

    assert business_hours_between(start, end) == Decimal("5.25")


def test_business_hours_between_skips_evenings_and_weekends() -> None:
    start = datetime(2026, 8, 7, 16, 0, tzinfo=UTC)  # Friday
    end = datetime(2026, 8, 10, 11, 30, tzinfo=UTC)  # Monday

    assert business_hours_between(start, end) == Decimal("3.5")


def test_business_hours_between_rejects_naive_datetimes() -> None:
    start = datetime(2026, 8, 3, 9, 0)
    end = datetime(2026, 8, 3, 10, 0)

    try:
        business_hours_between(start, end)
    except ValueError as error:
        assert "timezone-aware" in str(error)
    else:
        raise AssertionError("Expected a ValueError for naive datetimes")
