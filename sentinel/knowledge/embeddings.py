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
        Generate an embedding vector for text.
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
    Simple deterministic embedding provider for tests.
    """

    def __init__(
        self,
        dimension: int = 8,
    ) -> None:
        if dimension <= 0:
            raise ValueError(
                "Dimension must be positive."
            )

        self._dimension = dimension

    def embed(
        self,
        text: str,
    ) -> list[float]:
        """
        Generate a deterministic embedding.
        """
        value = float(len(text))

        return [
            value
            for _ in range(self._dimension)
        ]

    def dimension(self) -> int:
        return self._dimension