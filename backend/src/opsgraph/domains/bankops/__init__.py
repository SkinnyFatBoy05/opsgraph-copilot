"""Synthetic banking-operations domain."""

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from opsgraph.domains.bankops.schema import BANKOPS_SCHEMA


@dataclass(frozen=True)
class BankOpsDomain:
    name: Literal["bankops"] = "bankops"

    @property
    def documents_path(self) -> Path:
        project_root = Path(__file__).resolve().parents[5]
        return project_root / "data" / "bankops" / "documents"

    @property
    def schema(self) -> str:
        return BANKOPS_SCHEMA


__all__ = ["BANKOPS_SCHEMA", "BankOpsDomain"]
