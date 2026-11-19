from concurrent.futures import ThreadPoolExecutor

import pytest

from sentinel.knowledge.embeddings import (
    DummyEmbeddingProvider,
)


def test_embedding_dimension():
    provider = DummyEmbeddingProvider()

    vector = provider.embed("hello")

    assert len(vector) == provider.dimension()


def test_embedding_values():
    provider = DummyEmbeddingProvider(4)

    vector = provider.embed("abcd")

    assert vector == [4.0, 4.0, 4.0, 4.0]


def test_dimension():
    provider = DummyEmbeddingProvider(32)

    assert provider.dimension() == 32


def test_invalid_dimension():
    with pytest.raises(ValueError):
        DummyEmbeddingProvider(0)

def test_concurrent_embedding_calls() -> None:
    provider = DummyEmbeddingProvider(16)

    texts = [
        "Sentinel",
        "Knowledge",
        "Indexer",
        "Retriever",
        "Runtime",
        "Vector Store",
        "Kernel",
        "Platform",
    ]

    def embed(text: str) -> list[float]:
        return provider.embed(text)

    with ThreadPoolExecutor(max_workers=8) as executor:
        results = list(
            executor.map(embed, texts),
        )

    assert len(results) == len(texts)

    for text, vector in zip(texts, results, strict=True):
        assert len(vector) == 16
        assert vector == [float(len(text))] * 16