from hypothesis import given, strategies as st

from opsgraph.domains.awardlens.models import Money


@given(cents=st.integers(min_value=0, max_value=1_000_000))
def test_amounts_round_trip_as_integer_cents(cents: int) -> None:
    assert Money.from_cents(cents).cents == cents
