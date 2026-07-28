"""
Embedding interfaces for Sentinel OS.
"""

from __future__ import annotations

from abc import ABC, abstractmethod


class EmbeddingProvider(ABC):
    """
    Base interface for embedding providers.
    """

    @abstractmethod
    def embed(
        self,
        text: str,
    ) -> list[float]:
        """
        Generate an embedding vector for a single text.
        """
        raise NotImplementedError

    @abstractmethod
    def embed_many(
        self,
        texts: list[str],
    ) -> list[list[float]]:
        """
        Generate embeddings for multiple texts.
        """
        raise NotImplementedError

    @abstractmethod
    def dimension(self) -> int:
        """
        Return the embedding dimension.
        """
        raise NotImplementedError


class DummyEmbeddingProvider(EmbeddingProvider):
    """
    Deterministic embedding provider used for testing.
    """

    def __init__(
        self,
        dimension: int = 8,
    ) -> None:
        if dimension <= 0:
            raise ValueError("Dimension must be positive.")

        self._dimension = dimension

    def embed(
        self,
        text: str,
    ) -> list[float]:
        """
        Generate a deterministic embedding.
        """
        value = float(len(text))

        return [value] * self._dimension

    def embed_many(
        self,
        texts: list[str],
    ) -> list[list[float]]:
        """
        Generate embeddings for multiple texts.
        """
        return [self.embed(text) for text in texts]

    def dimension(self) -> int:
        """
        Return the embedding dimension.
        """
        return self._dimension