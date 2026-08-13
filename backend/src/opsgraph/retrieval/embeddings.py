"""No-cost deterministic local embeddings for development and CI."""

import re
from hashlib import sha256

import numpy as np

TOKEN_PATTERN = re.compile(r"[a-z0-9]+")


class HashingEmbeddingProvider:
    """Create normalized signed feature-hashing vectors without a model download."""

    def __init__(self, dimension: int = 384) -> None:
        if dimension < 32:
            raise ValueError("dimension must be at least 32")
        self._dimension = dimension

    @property
    def dimension(self) -> int:
        return self._dimension

    async def embed_documents(
        self, texts: tuple[str, ...]
    ) -> tuple[tuple[float, ...], ...]:
        return tuple(self._embed(text) for text in texts)

    async def embed_query(self, text: str) -> tuple[float, ...]:
        return self._embed(text)

    def _embed(self, text: str) -> tuple[float, ...]:
        tokens = TOKEN_PATTERN.findall(text.casefold())
        features = tokens + [f"{left}_{right}" for left, right in zip(tokens, tokens[1:])]
        vector = np.zeros(self.dimension, dtype=np.float32)
        for feature in features:
            digest = sha256(feature.encode("utf-8")).digest()
            index = int.from_bytes(digest[:8], "big") % self.dimension
            sign = 1.0 if digest[8] & 1 else -1.0
            vector[index] += sign
        norm = float(np.linalg.norm(vector))
        if norm:
            vector /= norm
        return tuple(float(value) for value in vector)
