from datetime import date

import pytest

from opsgraph.retrieval.contracts import SourceDocument
from opsgraph.retrieval.embeddings import HashingEmbeddingProvider
from opsgraph.retrieval.faiss_store import FaissVectorStore
from opsgraph.retrieval.service import RetrievalService


@pytest.fixture
async def service(tmp_path):
    retrieval = RetrievalService(
        embeddings=HashingEmbeddingProvider(dimension=128),
        store=FaissVectorStore(dimension=128, persist_path=tmp_path / "index"),
    )
    await retrieval.ingest(
        (
            SourceDocument(
                id="bank-policy",
                domain="bankops",
                text="# Complaint SLA\nPriority complaints require acknowledgement within four business hours.",
                effective_date=date(2026, 1, 1),
            ),
            SourceDocument(
                id="award-guide",
                domain="awardlens",
                text="# Hourly rates\nThe minimum hourly rate is calculated from the applicable award classification.",
                effective_date=date(2026, 7, 1),
            ),
        )
    )
    return retrieval


async def test_retrieval_never_crosses_domains(service) -> None:
    bank_hits = await service.search(
        domain="bankops",
        query="minimum hourly rate",
        top_k=8,
    )
    award_hits = await service.search(
        domain="awardlens",
        query="complaint acknowledgement",
        top_k=8,
    )

    assert bank_hits and all(hit.domain == "bankops" for hit in bank_hits)
    assert award_hits and all(hit.domain == "awardlens" for hit in award_hits)


async def test_retrieval_filters_future_documents(service) -> None:
    hits = await service.search(
        domain="awardlens",
        query="minimum hourly rate",
        top_k=8,
        effective_on=date(2026, 6, 30),
    )

    assert hits == ()


async def test_retrieval_rejects_more_than_eight_results(service) -> None:
    with pytest.raises(ValueError, match="between 1 and 8"):
        await service.search(domain="bankops", query="complaints", top_k=9)


async def test_faiss_metadata_survives_reload(tmp_path) -> None:
    index_path = tmp_path / "persisted"
    original = RetrievalService(
        embeddings=HashingEmbeddingProvider(dimension=64),
        store=FaissVectorStore(dimension=64, persist_path=index_path),
    )
    await original.ingest(
        (
            SourceDocument(
                id="policy",
                domain="bankops",
                text="# Evidence\nA synthetic evidence retention rule.",
                metadata={"owner": "Operations"},
            ),
        )
    )

    reloaded = RetrievalService(
        embeddings=HashingEmbeddingProvider(dimension=64),
        store=FaissVectorStore(dimension=64, persist_path=index_path),
    )
    hits = await reloaded.search(domain="bankops", query="evidence retention")

    assert hits[0].metadata["owner"] == "Operations"
