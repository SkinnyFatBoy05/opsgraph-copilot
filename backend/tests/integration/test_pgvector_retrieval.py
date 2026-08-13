import os
from uuid import uuid4

import pytest

from opsgraph.retrieval.contracts import SourceDocument
from opsgraph.retrieval.embeddings import HashingEmbeddingProvider
from opsgraph.retrieval.pgvector_store import PgVectorStore
from opsgraph.retrieval.service import RetrievalService


@pytest.mark.integration
async def test_pgvector_round_trip_and_domain_filter() -> None:
    database_url = os.getenv("OPSGRAPH_TEST_POSTGRES_URL")
    if not database_url:
        pytest.skip("OPSGRAPH_TEST_POSTGRES_URL is not configured")

    table_name = f"test_chunks_{uuid4().hex[:12]}"
    store = PgVectorStore(database_url, dimension=64, table_name=table_name)
    try:
        service = RetrievalService(
            embeddings=HashingEmbeddingProvider(dimension=64),
            store=store,
        )
        await store.initialize()
        await service.ingest(
            (
                SourceDocument(
                    id="bank-policy",
                    domain="bankops",
                    text="Priority complaints require acknowledgement in four business hours.",
                ),
                SourceDocument(
                    id="award-policy",
                    domain="awardlens",
                    text="The award classification determines the minimum hourly rate.",
                ),
            )
        )

        hits = await service.search(domain="bankops", query="priority complaints")

        assert hits and all(hit.domain == "bankops" for hit in hits)
    finally:
        await store.drop_table()
