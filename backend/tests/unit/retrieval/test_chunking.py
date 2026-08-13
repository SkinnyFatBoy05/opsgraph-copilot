from datetime import date

from opsgraph.retrieval.chunking import chunk_document
from opsgraph.retrieval.contracts import SourceDocument


def test_chunk_ids_are_stable_and_chunks_are_bounded() -> None:
    document = SourceDocument(
        id="policy-1",
        domain="bankops",
        text="# Scope\n" + "word " * 900,
        effective_date=date(2026, 1, 1),
    )

    first = chunk_document(document)
    second = chunk_document(document)

    assert [chunk.id for chunk in first] == [chunk.id for chunk in second]
    assert len(first) == 2
    assert all(len(chunk.text.split()) <= 600 for chunk in first)
    assert first[0].source_hash == first[1].source_hash


def test_chunking_preserves_heading_context() -> None:
    document = SourceDocument(
        id="policy-2",
        domain="bankops",
        text="# Complaint SLA\n\n## Priority\nPriority cases require action.",
    )

    chunks = chunk_document(document)

    assert chunks[0].heading == "Complaint SLA / Priority"
    assert "Priority cases require action." in chunks[0].text
