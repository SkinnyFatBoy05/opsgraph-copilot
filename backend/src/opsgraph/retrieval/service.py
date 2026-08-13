"""High-level ingestion and retrieval service."""

from datetime import date

from opsgraph.contracts.evidence import DomainName
from opsgraph.retrieval.chunking import chunk_document
from opsgraph.retrieval.contracts import (
    EmbeddingProvider,
    SearchHit,
    SourceDocument,
    VectorStore,
)
from opsgraph.observability.tracing import traced


class RetrievalService:
    def __init__(self, embeddings: EmbeddingProvider, store: VectorStore) -> None:
        self.embeddings = embeddings
        self.store = store

    async def ingest(self, documents: tuple[SourceDocument, ...]) -> int:
        chunks = tuple(
            chunk
            for document in documents
            for chunk in chunk_document(document)
        )
        if not chunks:
            return 0
        vectors = await self.embeddings.embed_documents(tuple(chunk.text for chunk in chunks))
        await self.store.upsert(chunks, vectors)
        return len(chunks)

    async def search(
        self,
        *,
        domain: DomainName,
        query: str,
        top_k: int = 5,
        effective_on: date | None = None,
    ) -> tuple[SearchHit, ...]:
        if not 1 <= top_k <= 8:
            raise ValueError("top_k must be between 1 and 8")
        if not query.strip():
            raise ValueError("query must not be empty")
        with traced(
            "opsgraph.retrieval",
            {"domain": domain, "query": query, "top_k": top_k},
        ):
            query_vector = await self.embeddings.embed_query(query)
            return await self.store.search(
                query_vector,
                domain=domain,
                top_k=top_k,
                effective_on=effective_on,
            )
