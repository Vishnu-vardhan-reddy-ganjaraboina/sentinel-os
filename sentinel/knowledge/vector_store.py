"""
Vector store interfaces for Sentinel OS.
"""

from __future__ import annotations
from sentinel.knowledge.similarity import DotProductSimilarity
from abc import ABC, abstractmethod

from sentinel.knowledge.chunk import Chunk
from sentinel.knowledge.similarity import (
    CosineSimilarity,
    SimilarityMetric,
)


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
        raise NotImplementedError

    @abstractmethod
    def delete(
        self,
        chunk_id: str,
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    def delete_document(
        self,
        document_id: str,
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    def search(
        self,
        embedding: list[float],
        *,
        limit: int = 5,
    ) -> list[Chunk]:
        raise NotImplementedError

    @abstractmethod
    def exists(
        self,
        chunk_id: str,
    ) -> bool:
        raise NotImplementedError

    @abstractmethod
    def get(
        self,
        chunk_id: str,
    ) -> Chunk | None:
        raise NotImplementedError

    @abstractmethod
    def list_chunks(self) -> list[Chunk]:
        raise NotImplementedError

    @abstractmethod
    def clear(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def __len__(self) -> int:
        raise NotImplementedError


class InMemoryVectorStore(VectorStore):
    """
    Production-quality in-memory vector store.

    Uses semantic similarity for retrieval.

    Intended for testing and lightweight deployments.
    """

    def __init__(
        self,
        similarity: SimilarityMetric | None = None,
    ) -> None:
        self._chunks: dict[str, Chunk] = {}
        self._embeddings: dict[str, list[float]] = {}
        self._similarity = similarity or CosineSimilarity()

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

    def delete_document(
        self,
        document_id: str,
    ) -> None:
        ids = [
            chunk_id
            for chunk_id, chunk in self._chunks.items()
            if chunk.document_id == document_id
        ]

        for chunk_id in ids:
            self.delete(chunk_id)

    def search(
        self,
        embedding: list[float],
        *,
        limit: int = 5,
    ) -> list[Chunk]:
        """
        Perform semantic similarity search.
        """
        ranked: list[tuple[float, Chunk]] = []

        for chunk_id, stored_embedding in self._embeddings.items():
            score = self._similarity.similarity(
                embedding,
                stored_embedding,
            )

            ranked.append(
                (
                    score,
                    self._chunks[chunk_id],
                )
            )

        ranked.sort(
            key=lambda item: item[0],
            reverse=True,
        )

        return [
            chunk
            for _, chunk in ranked[:limit]
        ]

    def exists(
        self,
        chunk_id: str,
    ) -> bool:
        return chunk_id in self._chunks

    def get(
        self,
        chunk_id: str,
    ) -> Chunk | None:
        return self._chunks.get(chunk_id)

    def list_chunks(self) -> list[Chunk]:
        return list(self._chunks.values())

    def clear(self) -> None:
        self._chunks.clear()
        self._embeddings.clear()

    def __len__(self) -> int:
        return len(self._chunks)