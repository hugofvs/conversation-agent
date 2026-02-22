from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from pydantic_ai import Embedder

from .models import RagSource


class VectorStore:
    def __init__(self, embedder: Embedder) -> None:
        self._embedder = embedder
        self._titles: list[str] = []
        self._contents: list[str] = []
        self._matrix: np.ndarray | None = None  # (n_docs, dim), L2-normalized

    async def load_corpus(self, path: str | Path) -> None:
        path = Path(path)
        with path.open() as f:
            chunks: list[dict] = json.load(f)

        self._titles = [c["title"] for c in chunks]
        self._contents = [c["content"] for c in chunks]

        result = await self._embedder.embed_documents(self._contents)
        matrix = np.array(result.embeddings, dtype=np.float32)
        # L2-normalize rows so dot product = cosine similarity
        norms = np.linalg.norm(matrix, axis=1, keepdims=True)
        norms = np.where(norms == 0, 1, norms)
        self._matrix = matrix / norms

    async def search(self, query: str, top_k: int = 3) -> list[RagSource]:
        if self._matrix is None or len(self._contents) == 0:
            return []

        result = await self._embedder.embed_query(query)
        q_vec = np.array(result.embeddings[0], dtype=np.float32)
        q_norm = np.linalg.norm(q_vec)
        if q_norm > 0:
            q_vec = q_vec / q_norm

        scores = self._matrix @ q_vec  # cosine similarities
        top_indices = np.argsort(scores)[::-1][:top_k]

        sources: list[RagSource] = []
        for idx in top_indices:
            score = float(scores[idx])
            if score < 0.3:
                continue
            sources.append(
                RagSource(
                    title=self._titles[idx],
                    content=self._contents[idx],
                    score=round(score, 3),
                )
            )
        return sources
