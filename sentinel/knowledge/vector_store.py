"""
Vector store interfaces for Sentinel OS.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from sentinel.knowledge.chunk import Chunk


class VectorStore(ABC):
    """
    Base interface for vector stores.
    """

    @abstractmethod
    def add(
        self,
        chunk: Chunk,
        embedding: list[float],
    ) -> None:
        """
        Store a chunk and its embedding.
        """
        raise NotImplementedError

    @abstractmethod
    def delete(
        self,
        chunk_id: str,
    ) -> None:
        """
        Remove a chunk.
        """
        raise NotImplementedError

    @abstractmethod
    def search(
        self,
        embedding: list[float],
        limit: int = 5,
    ) -> list[Chunk]:
        """
        Return the most similar chunks.
        """
        raise NotImplementedError

class InMemoryVectorStore(VectorStore):
    """
    Simple in-memory vector store for testing.
    """

    def __init__(self) -> None:
        self._chunks: dict[str, Chunk] = {}
        self._embeddings: dict[str, list[float]] = {}

    def add(
        self,
        chunk: Chunk,
        embedding: list[float],
    ) -> None:
        self._chunks[chunk.id] = chunk
        self._embeddings[chunk.id] = embedding

    def delete(
        self,
        chunk_id: str,
    ) -> None:
        self._chunks.pop(chunk_id, None)
        self._embeddings.pop(chunk_id, None)

    def search(
        self,
        embedding: list[float],
        limit: int = 5,
    ) -> list[Chunk]:
        """
        Temporary implementation.

        Returns the first N stored chunks.

        Real semantic similarity search will be added
        once we integrate FAISS or another vector DB.
        """
        return list(self._chunks.values())[:limit]