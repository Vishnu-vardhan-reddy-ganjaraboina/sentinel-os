"""
Production document indexer.

Coordinates chunking, embedding generation, and atomic vector-store
replacement while serializing operations for each document.
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from threading import RLock

from sentinel.knowledge.chunk import Chunk
from sentinel.knowledge.chunker import DocumentChunker
from sentinel.knowledge.document import Document
from sentinel.knowledge.embeddings import EmbeddingProvider
from sentinel.knowledge.vector_store import VectorStore


@dataclass(slots=True)
class _DocumentLockEntry:
    """Reference-counted lock for one document."""

    lock: RLock
    users: int = 0


class Indexer:
    """Coordinate safe, atomic document indexing."""

    def __init__(
        self,
        *,
        chunker: DocumentChunker,
        embedding_provider: EmbeddingProvider,
        vector_store: VectorStore,
    ) -> None:
        if type(vector_store).replace_document is VectorStore.replace_document:
            raise TypeError(
                "Indexer requires a vector store that implements "
                "atomic document replacement."
            )

        self._chunker = chunker
        self._embedding_provider = embedding_provider
        self._vector_store = vector_store

        self._lock = RLock()
        self._document_locks: dict[str, _DocumentLockEntry] = {}

    @property
    def chunker(self) -> DocumentChunker:
        return self._chunker

    @property
    def embedding_provider(self) -> EmbeddingProvider:
        return self._embedding_provider

    @property
    def vector_store(self) -> VectorStore:
        return self._vector_store

    def index(self, document: Document) -> list[Chunk]:
        """Prepare and atomically replace a document's indexed version."""
        with self._document_lock(document.id):
            prepared = self._prepare_document(document)
            self._replace_document(document.id, prepared)
            return [chunk for chunk, _ in prepared]

    def index_many(self, documents: Iterable[Document]) -> list[Chunk]:
        """Index multiple documents independently."""
        indexed_chunks: list[Chunk] = []

        for document in documents:
            indexed_chunks.extend(self.index(document))

        return indexed_chunks

    def remove(self, document_id: str) -> None:
        """Remove all indexed data belonging to a document."""
        with self._document_lock(document_id):
            self._vector_store.delete_document(document_id)

    def reindex(self, document: Document) -> list[Chunk]:
        """Atomically replace an existing document version."""
        with self._document_lock(document.id):
            prepared = self._prepare_document(document)
            self._replace_document(document.id, prepared)
            return [chunk for chunk, _ in prepared]

    def _prepare_document(
        self,
        document: Document,
    ) -> list[tuple[Chunk, list[float]]]:
        """Prepare all chunks and embeddings without mutating storage."""
        chunks = self._chunker.chunk(document)

        seen_ids: set[str] = set()

        for chunk in chunks:
            if chunk.document_id != document.id:
                raise ValueError(
                    f"Chunk document ID does not match document ID "
                    f"{document.id!r}."
                )

            if chunk.id in seen_ids:
                raise ValueError(
                    f"Duplicate chunk ID {chunk.id!r} generated for document."
                )

            seen_ids.add(chunk.id)

        embeddings = self._embedding_provider.embed_many(
            [chunk.text for chunk in chunks]
        )

        if len(embeddings) != len(chunks):
            raise ValueError(
                "Embedding provider returned a different number of embeddings "
                "than chunks."
            )

        return [
            (chunk, [float(value) for value in embedding])
            for chunk, embedding in zip(chunks, embeddings, strict=True)
        ]

    def _replace_document(
        self,
        document_id: str,
        prepared: list[tuple[Chunk, list[float]]],
    ) -> None:
        """Delegate atomic replacement to the vector store."""
        self._vector_store.replace_document(document_id, prepared)

    @contextmanager
    def _document_lock(self, document_id: str) -> Iterator[None]:
        """Acquire a stable per-document lock and clean it up safely."""
        self._validate_document_id(document_id)

        with self._lock:
            entry = self._document_locks.get(document_id)

            if entry is None:
                entry = _DocumentLockEntry(lock=RLock())
                self._document_locks[document_id] = entry

            entry.users += 1

        acquired = False

        try:
            entry.lock.acquire()
            acquired = True
            yield
        finally:
            if acquired:
                entry.lock.release()

            with self._lock:
                entry.users -= 1

                current = self._document_locks.get(document_id)

                if current is entry and entry.users == 0:
                    del self._document_locks[document_id]

    @staticmethod
    def _validate_document_id(document_id: str) -> None:
        if not isinstance(document_id, str):
            raise TypeError("Document ID must be a string.")

        if not document_id.strip():
            raise ValueError("Document ID cannot be empty.")
