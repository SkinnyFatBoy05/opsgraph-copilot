"""Grounded document ingestion and vector retrieval."""

from opsgraph.retrieval.contracts import DocumentChunk, SearchHit, SourceDocument
from opsgraph.retrieval.embeddings import HashingEmbeddingProvider
from opsgraph.retrieval.service import RetrievalService

__all__ = [
    "DocumentChunk",
    "HashingEmbeddingProvider",
    "RetrievalService",
    "SearchHit",
    "SourceDocument",
]
