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