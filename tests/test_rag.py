"""Unit tests for the VectorStore (RAG search)."""
from __future__ import annotations

import numpy as np
import pytest

from conversation_agent.models import RagSource
from conversation_agent.rag import VectorStore


class FakeEmbedder:
    """Embedder stub that returns deterministic vectors."""

    def __init__(self, dim: int = 4):
        self._dim = dim
        self._call_count = 0

    async def embed_documents(self, docs: list[str]):
        # Return orthogonal-ish vectors for each doc
        vecs = []
        for i, _ in enumerate(docs):
            v = np.zeros(self._dim, dtype=np.float32)
            v[i % self._dim] = 1.0
            vecs.append(v.tolist())

        class Result:
            embeddings = vecs

        return Result()

    async def embed_query(self, query: str):
        # Return a vector that aligns with the first doc
        v = np.zeros(self._dim, dtype=np.float32)
        v[0] = 1.0

        class Result:
            embeddings = [v.tolist()]

        return Result()


@pytest.fixture
def embedder():
    return FakeEmbedder(dim=4)


async def test_search_returns_results(embedder, tmp_path):
    corpus = tmp_path / "corpus.json"
    import json

    corpus.write_text(json.dumps([
        {"title": "Doc A", "content": "Alpha content"},
        {"title": "Doc B", "content": "Beta content"},
    ]))

    store = VectorStore(embedder)
    await store.load_corpus(corpus)

    results = await store.search("alpha", top_k=2)
    assert len(results) >= 1
    assert isinstance(results[0], RagSource)
    assert results[0].title == "Doc A"
    assert results[0].score > 0.3


async def test_search_empty_matrix(embedder):
    store = VectorStore(embedder)
    # _matrix is None — should return empty
    results = await store.search("anything")
    assert results == []


async def test_search_filters_low_scores(embedder, tmp_path):
    import json

    corpus = tmp_path / "corpus.json"
    corpus.write_text(json.dumps([
        {"title": "Doc A", "content": "Alpha"},
        {"title": "Doc B", "content": "Beta"},
        {"title": "Doc C", "content": "Gamma"},
    ]))

    store = VectorStore(embedder)
    await store.load_corpus(corpus)

    # Our fake embedder makes query align with Doc A only (dim 0),
    # so Doc B (dim 1) and Doc C (dim 2) get score 0.0 and are filtered
    results = await store.search("alpha", top_k=3)
    assert all(r.score >= 0.3 for r in results)


async def test_search_top_k_limits_results(embedder, tmp_path):
    import json

    # Create 4 docs where all align with the query (same dimension)
    corpus = tmp_path / "corpus.json"
    corpus.write_text(json.dumps([
        {"title": f"Doc {i}", "content": f"Content {i}"} for i in range(4)
    ]))

    # Override embedder to make all docs similar to query
    class AllSameEmbedder:
        async def embed_documents(self, docs):
            class Result:
                embeddings = [[1.0, 0.0, 0.0, 0.0]] * len(docs)
            return Result()

        async def embed_query(self, query):
            class Result:
                embeddings = [[1.0, 0.0, 0.0, 0.0]]
            return Result()

    store = VectorStore(AllSameEmbedder())
    await store.load_corpus(corpus)

    results = await store.search("anything", top_k=2)
    assert len(results) <= 2


async def test_load_corpus_normalizes_vectors(embedder, tmp_path):
    import json

    corpus = tmp_path / "corpus.json"
    corpus.write_text(json.dumps([
        {"title": "Doc A", "content": "Alpha"},
    ]))

    store = VectorStore(embedder)
    await store.load_corpus(corpus)

    # After normalization, rows should have unit norm
    assert store._matrix is not None
    norms = np.linalg.norm(store._matrix, axis=1)
    np.testing.assert_allclose(norms, 1.0, atol=1e-6)
