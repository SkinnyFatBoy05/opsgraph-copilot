"""PostgreSQL/pgvector retrieval adapter for the production profile."""

import re
from datetime import date

import numpy as np
import psycopg
from pgvector.psycopg import register_vector_async
from psycopg.types.json import Jsonb

from opsgraph.contracts.evidence import DomainName
from opsgraph.retrieval.contracts import DocumentChunk, SearchHit

IDENTIFIER = re.compile(r"^[a-z][a-z0-9_]{0,62}$")


class PgVectorStore:
    def __init__(
        self,
        database_url: str,
        *,
        dimension: int,
        table_name: str = "opsgraph_document_chunks",
    ) -> None:
        if not IDENTIFIER.fullmatch(table_name):
            raise ValueError("table_name must be a safe PostgreSQL identifier")
        self.database_url = database_url
        self.dimension = dimension
        self.table_name = table_name

    async def initialize(self) -> None:
        async with await psycopg.AsyncConnection.connect(self.database_url) as connection:
            async with connection.cursor() as cursor:
                await cursor.execute("CREATE EXTENSION IF NOT EXISTS vector")
            await connection.commit()
            await register_vector_async(connection)
            async with connection.cursor() as cursor:
                await cursor.execute(
                    f"""
                    CREATE TABLE IF NOT EXISTS {self.table_name} (
                        id TEXT PRIMARY KEY,
                        document_id TEXT NOT NULL,
                        domain TEXT NOT NULL,
                        text TEXT NOT NULL,
                        source_hash TEXT NOT NULL,
                        heading TEXT,
                        source_uri TEXT,
                        version TEXT,
                        effective_date DATE,
                        owner TEXT,
                        metadata JSONB NOT NULL,
                        embedding VECTOR({self.dimension}) NOT NULL
                    )
                    """
                )
                await cursor.execute(
                    f"CREATE INDEX IF NOT EXISTS {self.table_name}_embedding_hnsw "
                    f"ON {self.table_name} USING hnsw (embedding vector_cosine_ops)"
                )

    async def upsert(
        self,
        chunks: tuple[DocumentChunk, ...],
        vectors: tuple[tuple[float, ...], ...],
    ) -> None:
        if len(chunks) != len(vectors):
            raise ValueError("each chunk must have one vector")
        async with await psycopg.AsyncConnection.connect(self.database_url) as connection:
            await register_vector_async(connection)
            async with connection.cursor() as cursor:
                await cursor.executemany(
                    f"""
                    INSERT INTO {self.table_name} (
                        id, document_id, domain, text, source_hash, heading,
                        source_uri, version, effective_date, owner, metadata, embedding
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO UPDATE SET
                        text = EXCLUDED.text,
                        metadata = EXCLUDED.metadata,
                        embedding = EXCLUDED.embedding
                    """,
                    [
                        (
                            chunk.id,
                            chunk.document_id,
                            chunk.domain,
                            chunk.text,
                            chunk.source_hash,
                            chunk.heading,
                            chunk.source_uri,
                            chunk.version,
                            chunk.effective_date,
                            chunk.owner,
                            Jsonb(chunk.metadata),
                            np.asarray(vector, dtype=np.float32),
                        )
                        for chunk, vector in zip(chunks, vectors)
                    ],
                )

    async def search(
        self,
        query_vector: tuple[float, ...],
        *,
        domain: DomainName,
        top_k: int,
        effective_on: date | None = None,
    ) -> tuple[SearchHit, ...]:
        vector = np.asarray(query_vector, dtype=np.float32)
        filters = "domain = %s"
        parameters: list[object] = [vector, domain]
        if effective_on:
            filters += " AND (effective_date IS NULL OR effective_date <= %s)"
            parameters.append(effective_on)
        parameters.extend((vector, top_k))

        async with await psycopg.AsyncConnection.connect(self.database_url) as connection:
            await register_vector_async(connection)
            async with connection.cursor() as cursor:
                await cursor.execute(
                    f"""
                    SELECT id, document_id, domain, text, source_hash, heading,
                           source_uri, version, effective_date, owner, metadata,
                           GREATEST(0, LEAST(1, 1 - (embedding <=> %s))) AS score
                    FROM {self.table_name}
                    WHERE {filters}
                    ORDER BY embedding <=> %s
                    LIMIT %s
                    """,
                    parameters,
                )
                rows = await cursor.fetchall()

        return tuple(
            SearchHit(
                id=row[0],
                document_id=row[1],
                domain=row[2],
                text=row[3],
                source_hash=row[4],
                heading=row[5],
                source_uri=row[6],
                version=row[7],
                effective_date=row[8],
                owner=row[9],
                metadata=row[10],
                score=float(row[11]),
            )
            for row in rows
        )

    async def drop_table(self) -> None:
        async with await psycopg.AsyncConnection.connect(self.database_url) as connection:
            async with connection.cursor() as cursor:
                await cursor.execute(f"DROP TABLE IF EXISTS {self.table_name}")
