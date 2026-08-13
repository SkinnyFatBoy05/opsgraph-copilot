from decimal import Decimal

import pytest

from opsgraph.observability.costs import ModelPrice, PriceNotConfigured, estimate_cost


def test_fake_provider_cost_is_exactly_zero() -> None:
    assert estimate_cost("fake", "deterministic-v1", 1_000, 1_000) == Decimal("0")


def test_cost_uses_decimal_price_table() -> None:
    price_table = {
        ("provider", "model"): ModelPrice(
            input_per_million=Decimal("1.25"),
            output_per_million=Decimal("5.00"),
        )
    }

    assert estimate_cost("provider", "model", 1_000, 1_000, price_table) == Decimal(
        "0.00625000"
    )


def test_unknown_model_is_not_silently_priced_as_free() -> None:
    with pytest.raises(PriceNotConfigured):
        estimate_cost("unknown", "unknown", 10, 10)


def test_no_observed_token_usage_has_zero_cost_without_a_price_entry() -> None:
    assert estimate_cost("bedrock", "configured-at-runtime", 0, 0) == Decimal("0")


@pytest.mark.parametrize("input_tokens,output_tokens", [(-1, 0), (0, -1)])
def test_negative_usage_is_rejected(input_tokens: int, output_tokens: int) -> None:
    with pytest.raises(ValueError):
        estimate_cost("fake", "deterministic-v1", input_tokens, output_tokens)
