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

    A vector store maintains Chunk/embedding pairs.
    """

    @abstractmethod
    def add(
        self,
        chunk: Chunk,
        embedding: list[float],
    ) -> None:
        """Add or replace one chunk."""
        raise NotImplementedError

    @abstractmethod
    def delete(
        self,
        chunk_id: str,
    ) -> None:
        """Delete one chunk."""
        raise NotImplementedError

    @abstractmethod
    def delete_document(
        self,
        document_id: str,
    ) -> None:
        """Delete all chunks belonging to a document."""
        raise NotImplementedError

    @abstractmethod
    def search(
        self,
        embedding: list[float],
        *,
        limit: int = 5,
    ) -> list[Chunk]:
        """Search by vector similarity."""
        raise NotImplementedError

    @abstractmethod
    def exists(
        self,
        chunk_id: str,
    ) -> bool:
        """Return whether a chunk exists."""
        raise NotImplementedError

    @abstractmethod
    def get(
        self,
        chunk_id: str,
    ) -> Chunk | None:
        """Retrieve a chunk."""
        raise NotImplementedError

    @abstractmethod
    def list_chunks(self) -> list[Chunk]:
        """Return all chunks."""
        raise NotImplementedError

    @abstractmethod
    def clear(self) -> None:
        """Remove all chunks."""
        raise NotImplementedError

    @abstractmethod
    def connect(self) -> None:
        """Connect the store."""
        raise NotImplementedError

    @abstractmethod
    def close(self) -> None:
        """Close the store."""
        raise NotImplementedError

    @abstractmethod
    def __len__(self) -> int:
        """Return the number of chunks."""
        raise NotImplementedError

    def replace_document(
        self,
        document_id: str,
        chunks: list[tuple[Chunk, list[float]]],
    ) -> None:
        """
        Replace all chunks belonging to a document.

        This method is deliberately concrete rather than abstract to preserve
        compatibility with existing custom VectorStore implementations.

        Implementations that can guarantee true atomic replacement should
        override it.
        """
        self.delete_document(document_id)

        for chunk, embedding in chunks:
            self.add(
                chunk,
                embedding,
            )


class InMemoryVectorStore(VectorStore):
    """
    Thread-safe in-memory vector store.

    Chunk/embedding pairs are maintained atomically.
    """

    def __init__(
        self,
        similarity: SimilarityMetric | None = None,
    ) -> None:
        self._lock = RLock()

        self._chunks: dict[str, Chunk] = {}
        self._embeddings: dict[str, list[float]] = {}

        self._similarity = (
            similarity
            if similarity is not None
            else CosineSimilarity()
        )

    def add(
        self,
        chunk: Chunk,
        embedding: list[float],
    ) -> None:
        """
        Add or replace a chunk and embedding atomically.
        """
        copied_embedding = [
            float(value)
            for value in embedding
        ]

        if not copied_embedding:
            raise ValueError("Embedding cannot be empty.")
        if not all(isfinite(value) for value in copied_embedding):
            raise ValueError("Embedding must contain only finite values.")

        with self._lock:
            self._chunks[chunk.id] = chunk
            self._embeddings[chunk.id] = copied_embedding

    def delete(
        self,
        chunk_id: str,
    ) -> None:
        """Delete a chunk and embedding atomically."""
        with self._lock:
            self._chunks.pop(
                chunk_id,
                None,
            )

            self._embeddings.pop(
                chunk_id,
                None,
            )

    def delete_document(
        self,
        document_id: str,
    ) -> None:
        """Delete all chunks belonging to a document atomically."""
        with self._lock:
            chunk_ids = [
                chunk_id
                for chunk_id, chunk in self._chunks.items()
                if chunk.document_id == document_id
            ]

            for chunk_id in chunk_ids:
                self._chunks.pop(
                    chunk_id,
                    None,
                )

                self._embeddings.pop(
                    chunk_id,
                    None,
                )

    def replace_document(
        self,
        document_id: str,
        chunks: list[tuple[Chunk, list[float]]],
    ) -> None:
        """
        Atomically replace all chunks belonging to a document.

        Validation/copying occurs before acquiring the mutation lock so
        invalid input cannot destroy the existing version.
        """
        if not document_id.strip():
            raise ValueError("Document id cannot be empty.")

        prepared: list[tuple[Chunk, list[float]]] = []

        for chunk, embedding in chunks:
            if chunk.document_id != document_id:
                raise ValueError(
                    "Chunk document ID does not match replacement "
                    f"document ID '{document_id}'."
                )

            values = [float(value) for value in embedding]
            if not values:
                raise ValueError("Embedding cannot be empty.")
            if not all(isfinite(value) for value in values):
                raise ValueError("Embedding must contain only finite values.")

            prepared.append((chunk, values))

        new_ids = {
            chunk.id
            for chunk, _ in prepared
        }

        if len(new_ids) != len(prepared):
            raise ValueError(
                "Replacement contains duplicate chunk IDs."
            )

        with self._lock:
            for chunk, _ in prepared:
                existing = self._chunks.get(chunk.id)
                if (
                    existing is not None
                    and existing.document_id != document_id
                ):
                    raise ValueError(
                        f"Chunk id {chunk.id!r} belongs to another document."
                    )

            old_ids = [
                chunk_id
                for chunk_id, chunk in self._chunks.items()
                if chunk.document_id == document_id
            ]

            for chunk_id in old_ids:
                self._chunks.pop(
                    chunk_id,
                    None,
                )

                self._embeddings.pop(
                    chunk_id,
                    None,
                )

            for chunk, embedding in prepared:
                self._chunks[chunk.id] = chunk
                self._embeddings[chunk.id] = embedding

    def search(
        self,
        embedding: list[float],
        *,
        limit: int = 5,
    ) -> list[Chunk]:
        """
        Return the most similar chunks.

        A stable snapshot is captured before similarity calculations.
        """
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
            snapshot = [
                (
                    chunk,
                    list(
                        self._embeddings[chunk_id]
                    ),
                )
                for chunk_id, chunk in self._chunks.items()
                if chunk_id in self._embeddings
            ]

        scored: list[tuple[float, Chunk]] = []

        for chunk, stored_embedding in snapshot:
            score = self._similarity.similarity(
                query_embedding,
                stored_embedding,
            )

            scored.append(
                (
                    score,
                    chunk,
                )
            )

        scored.sort(
            key=lambda item: item[0],
            reverse=True,
        )

        return [
            chunk
            for _, chunk in scored[:limit]
        ]

    def exists(
        self,
        chunk_id: str,
    ) -> bool:
        with self._lock:
            return chunk_id in self._chunks

    def get(
        self,
        chunk_id: str,
    ) -> Chunk | None:
        with self._lock:
            return self._chunks.get(chunk_id)

    def list_chunks(self) -> list[Chunk]:
        with self._lock:
            return list(
                self._chunks.values()
            )

    def clear(self) -> None:
        with self._lock:
            self._chunks.clear()
            self._embeddings.clear()

    def connect(self) -> None:
        return None

    def close(self) -> None:
        return None

    def __len__(self) -> int:
        with self._lock:
            return len(self._chunks)