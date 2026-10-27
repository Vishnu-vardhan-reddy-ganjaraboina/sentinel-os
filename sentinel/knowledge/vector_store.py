"""
Vector store interfaces for Sentinel OS.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from math import isfinite
from threading import RLock

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

    def replace_document(
        self,
        document_id: str,
        chunks_with_embeddings: list[tuple[Chunk, list[float]]],
    ) -> None:
        """Replace one document's chunks when supported by the store."""
        raise NotImplementedError(
            f"{type(self).__name__} does not support document replacement."
        )

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

    def connect(self) -> None:
        """
        Connect the vector store to its underlying resources.

        In-memory stores do not require an explicit connection.
        Persistent implementations can override this method.
        """
        return None

    def close(self) -> None:
        """
        Release resources owned by the vector store.

        In-memory stores do not require explicit cleanup.
        Persistent implementations can override this method.
        """
        return None

    @abstractmethod
    def __len__(self) -> int:
        raise NotImplementedError


class InMemoryVectorStore(VectorStore):
    """
    Production-quality in-memory vector store.

    Uses semantic similarity for retrieval and a reentrant lock to keep
    reads and writes consistent during concurrent document replacement.
    """

    def __init__(
        self,
        similarity: SimilarityMetric | None = None,
    ) -> None:
        self._chunks: dict[str, Chunk] = {}
        self._embeddings: dict[str, list[float]] = {}
        self._similarity = similarity or CosineSimilarity()
        self._lock = RLock()

    def add(self, chunk: Chunk, embedding: list[float]) -> None:
        """Add or replace a chunk and its validated embedding."""
        values = [float(value) for value in embedding]
        if not values:
            raise ValueError("Embedding cannot be empty.")
        if not all(isfinite(value) for value in values):
            raise ValueError("Embedding must contain only finite values.")

        with self._lock:
            self._chunks[chunk.id] = chunk
            self._embeddings[chunk.id] = values

    def delete(self, chunk_id: str) -> None:
        """Delete a chunk if it exists."""
        with self._lock:
            self._chunks.pop(chunk_id, None)
            self._embeddings.pop(chunk_id, None)

    def delete_document(self, document_id: str) -> None:
        """Delete every chunk belonging to a document."""
        with self._lock:
            ids = [
                chunk_id
                for chunk_id, chunk in self._chunks.items()
                if chunk.document_id == document_id
            ]
            for chunk_id in ids:
                self._chunks.pop(chunk_id, None)
                self._embeddings.pop(chunk_id, None)

    def replace_document(
        self,
        document_id: str,
        chunks_with_embeddings: list[tuple[Chunk, list[float]]],
    ) -> None:
        """Validate and atomically replace all chunks for one document."""
        if not document_id.strip():
            raise ValueError("Document id cannot be empty.")

        staged_chunks: dict[str, Chunk] = {}
        staged_embeddings: dict[str, list[float]] = {}

        for chunk, embedding in chunks_with_embeddings:
            if chunk.document_id != document_id:
                raise ValueError(
                    "Replacement chunk has a different document id."
                )
            if chunk.id in staged_chunks:
                raise ValueError(
                    f"Duplicate replacement chunk id: {chunk.id}"
                )

            values = [float(value) for value in embedding]
            if not values:
                raise ValueError("Embedding cannot be empty.")
            if not all(isfinite(value) for value in values):
                raise ValueError(
                    "Embedding must contain only finite values."
                )

            staged_chunks[chunk.id] = chunk
            staged_embeddings[chunk.id] = values

        with self._lock:
            for chunk_id in staged_chunks:
                existing = self._chunks.get(chunk_id)
                if (
                    existing is not None
                    and existing.document_id != document_id
                ):
                    raise ValueError(
                        f"Chunk id {chunk_id!r} belongs to another document."
                    )

            retained_chunks = {
                key: value
                for key, value in self._chunks.items()
                if value.document_id != document_id
            }
            retained_embeddings = {
                key: value
                for key, value in self._embeddings.items()
                if key in retained_chunks
            }
            retained_chunks.update(staged_chunks)
            retained_embeddings.update(staged_embeddings)

            self._chunks = retained_chunks
            self._embeddings = retained_embeddings

    def search(
        self,
        embedding: list[float],
        *,
        limit: int = 5,
    ) -> list[Chunk]:
        """Perform semantic similarity search."""
        if limit <= 0:
            return []

        query_embedding = [float(value) for value in embedding]
        if not query_embedding:
            raise ValueError("Query embedding cannot be empty.")
        if not all(isfinite(value) for value in query_embedding):
            raise ValueError(
                "Query embedding must contain only finite values."
            )

        with self._lock:
            ranked: list[tuple[float, Chunk]] = []
            for chunk_id, stored_embedding in self._embeddings.items():
                score = self._similarity.similarity(
                    query_embedding,
                    stored_embedding,
                )
                ranked.append((score, self._chunks[chunk_id]))

            ranked.sort(key=lambda item: item[0], reverse=True)
            return [chunk for _, chunk in ranked[:limit]]

    def exists(self, chunk_id: str) -> bool:
        with self._lock:
            return chunk_id in self._chunks

    def get(self, chunk_id: str) -> Chunk | None:
        with self._lock:
            return self._chunks.get(chunk_id)

    def list_chunks(self) -> list[Chunk]:
        with self._lock:
            return list(self._chunks.values())

    def clear(self) -> None:
        with self._lock:
            self._chunks.clear()
            self._embeddings.clear()

    def __len__(self) -> int:
        with self._lock:
            return len(self._chunks)
