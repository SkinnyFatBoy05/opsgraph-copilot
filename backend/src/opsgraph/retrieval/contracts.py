"""Provider-neutral retrieval contracts."""

from datetime import date
from hashlib import sha256
from typing import Any, Protocol

from pydantic import BaseModel, ConfigDict, Field, field_validator

from opsgraph.contracts.evidence import DomainName


class SourceDocument(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str = Field(min_length=1)
    domain: DomainName
    text: str = Field(min_length=1)
    title: str | None = None
    source_uri: str | None = None
    version: str | None = None
    effective_date: date | None = None
    owner: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("metadata", mode="before")
    @classmethod
    def copy_metadata(cls, value: dict[str, Any]) -> dict[str, Any]:
        return dict(value)

    @property
    def source_hash(self) -> str:
        return sha256(self.text.encode("utf-8")).hexdigest()


class DocumentChunk(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str = Field(min_length=1)
    document_id: str = Field(min_length=1)
    domain: DomainName
    text: str = Field(min_length=1)
    source_hash: str = Field(min_length=64, max_length=64)
    heading: str | None = None
    source_uri: str | None = None
    version: str | None = None
    effective_date: date | None = None
    owner: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class SearchHit(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str
    document_id: str
    domain: DomainName
    text: str
    score: float = Field(ge=0, le=1)
    source_hash: str
    heading: str | None = None
    source_uri: str | None = None
    version: str | None = None
    effective_date: date | None = None
    owner: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class EmbeddingProvider(Protocol):
    @property
    def dimension(self) -> int: ...

    async def embed_documents(
        self, texts: tuple[str, ...]
    ) -> tuple[tuple[float, ...], ...]: ...

    async def embed_query(self, text: str) -> tuple[float, ...]: ...


class VectorStore(Protocol):
    async def upsert(
        self,
        chunks: tuple[DocumentChunk, ...],
        vectors: tuple[tuple[float, ...], ...],
    ) -> None: ...

    async def search(
        self,
        query_vector: tuple[float, ...],
        *,
        domain: DomainName,
        top_k: int,
        effective_on: date | None = None,
    ) -> tuple[SearchHit, ...]: ...
