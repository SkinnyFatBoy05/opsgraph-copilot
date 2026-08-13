"""Evidence and domain contracts."""

from datetime import date
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

DomainName = Literal["bankops", "awardlens"]
EvidenceKind = Literal["document", "sql", "calculation"]


class EvidenceRef(BaseModel):
    """A frozen reference to information used to form an answer."""

    model_config = ConfigDict(frozen=True)

    id: str = Field(min_length=1)
    domain: DomainName
    text: str = Field(min_length=1)
    kind: EvidenceKind = "document"
    title: str | None = None
    source_uri: str | None = None
    section: str | None = None
    effective_date: date | None = None
    score: float | None = Field(default=None, ge=0, le=1)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("metadata", mode="before")
    @classmethod
    def copy_metadata(cls, value: dict[str, Any]) -> dict[str, Any]:
        return dict(value)
