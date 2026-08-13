"""Local FAISS vector store with portable, immutable metadata snapshots."""

import json
from datetime import date
from pathlib import Path

import faiss
import numpy as np

from opsgraph.contracts.evidence import DomainName
from opsgraph.retrieval.contracts import DocumentChunk, SearchHit


class FaissVectorStore:
    def __init__(self, dimension: int, persist_path: Path | None = None) -> None:
        self.dimension = dimension
        self.persist_path = persist_path
        self._chunks: dict[str, DocumentChunk] = {}
        self._vectors: dict[str, tuple[float, ...]] = {}
        self._ordered_ids: tuple[str, ...] = ()
        self._index = faiss.IndexFlatIP(dimension)
        if persist_path and (persist_path / "metadata.json").exists():
            self._load()

    async def upsert(
        self,
        chunks: tuple[DocumentChunk, ...],
        vectors: tuple[tuple[float, ...], ...],
    ) -> None:
        if len(chunks) != len(vectors):
            raise ValueError("each chunk must have one vector")
        for chunk, vector in zip(chunks, vectors):
            if len(vector) != self.dimension:
                raise ValueError(f"expected vector dimension {self.dimension}")
            self._chunks[chunk.id] = chunk
            self._vectors[chunk.id] = tuple(vector)
        self._rebuild()
        if self.persist_path:
            self._persist()

    async def search(
        self,
        query_vector: tuple[float, ...],
        *,
        domain: DomainName,
        top_k: int,
        effective_on: date | None = None,
    ) -> tuple[SearchHit, ...]:
        if len(query_vector) != self.dimension:
            raise ValueError(f"expected vector dimension {self.dimension}")
        if self._index.ntotal == 0:
            return ()

        query = np.asarray([query_vector], dtype=np.float32)
        scores, indices = self._index.search(query, int(self._index.ntotal))
        hits: list[SearchHit] = []
        for score, index in zip(scores[0], indices[0]):
            if index < 0:
                continue
            chunk = self._chunks[self._ordered_ids[int(index)]]
            if chunk.domain != domain:
                continue
            if effective_on and chunk.effective_date and chunk.effective_date > effective_on:
                continue
            hits.append(_to_hit(chunk, float(score)))
            if len(hits) == top_k:
                break
        return tuple(hits)

    def _rebuild(self) -> None:
        self._ordered_ids = tuple(sorted(self._chunks))
        self._index = faiss.IndexFlatIP(self.dimension)
        if self._ordered_ids:
            vectors = np.asarray(
                [self._vectors[chunk_id] for chunk_id in self._ordered_ids],
                dtype=np.float32,
            )
            self._index.add(vectors)

    def _persist(self) -> None:
        assert self.persist_path is not None
        self.persist_path.mkdir(parents=True, exist_ok=True)
        index_temp = self.persist_path / "index.faiss.tmp"
        metadata_temp = self.persist_path / "metadata.json.tmp"
        faiss.write_index(self._index, str(index_temp))
        snapshot = {
            "dimension": self.dimension,
            "ordered_ids": self._ordered_ids,
            "chunks": [
                self._chunks[chunk_id].model_dump(mode="json")
                for chunk_id in self._ordered_ids
            ],
        }
        metadata_temp.write_text(
            json.dumps(snapshot, sort_keys=True, separators=(",", ":")),
            encoding="utf-8",
        )
        index_temp.replace(self.persist_path / "index.faiss")
        metadata_temp.replace(self.persist_path / "metadata.json")

    def _load(self) -> None:
        assert self.persist_path is not None
        snapshot = json.loads((self.persist_path / "metadata.json").read_text(encoding="utf-8"))
        if snapshot["dimension"] != self.dimension:
            raise ValueError("persisted FAISS dimension does not match")
        self._index = faiss.read_index(str(self.persist_path / "index.faiss"))
        chunks = tuple(DocumentChunk.model_validate(value) for value in snapshot["chunks"])
        self._chunks = {chunk.id: chunk for chunk in chunks}
        self._ordered_ids = tuple(snapshot["ordered_ids"])
        self._vectors = {
            chunk_id: tuple(float(value) for value in self._index.reconstruct(index))
            for index, chunk_id in enumerate(self._ordered_ids)
        }


def _to_hit(chunk: DocumentChunk, score: float) -> SearchHit:
    return SearchHit(
        **chunk.model_dump(),
        score=max(0.0, min(1.0, score)),
    )
