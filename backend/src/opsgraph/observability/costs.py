"""Versioned Decimal-based model cost estimation."""

from dataclasses import dataclass
from decimal import Decimal
from typing import Mapping

PRICE_TABLE_VERSION = "2026-08-08"
MILLION = Decimal("1000000")


@dataclass(frozen=True)
class ModelPrice:
    input_per_million: Decimal
    output_per_million: Decimal


class PriceNotConfigured(LookupError):
    """Raised when a provider/model pair has no reviewed price entry."""


DEFAULT_PRICE_TABLE: Mapping[tuple[str, str], ModelPrice] = {
    ("fake", "deterministic-v1"): ModelPrice(Decimal("0"), Decimal("0")),
    ("ollama", "local"): ModelPrice(Decimal("0"), Decimal("0")),
}


def estimate_cost(
    provider: str,
    model: str,
    input_tokens: int,
    output_tokens: int,
    price_table: Mapping[tuple[str, str], ModelPrice] = DEFAULT_PRICE_TABLE,
) -> Decimal:
    """Estimate model cost exactly; unknown prices never masquerade as free."""

    if input_tokens < 0 or output_tokens < 0:
        raise ValueError("token counts must be non-negative")
    if input_tokens == 0 and output_tokens == 0:
        return Decimal("0")
    key = (provider.casefold(), model.casefold())
    try:
        price = price_table[key]
    except KeyError as error:
        raise PriceNotConfigured(f"no price configured for {provider}/{model}") from error
    return (
        Decimal(input_tokens) * price.input_per_million
        + Decimal(output_tokens) * price.output_per_million
    ) / MILLION
