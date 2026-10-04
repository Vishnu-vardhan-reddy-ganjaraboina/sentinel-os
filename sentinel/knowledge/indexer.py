"""
Indexer implementation.

The Indexer transforms documents into searchable knowledge by coordinating
chunking, embedding generation, and vector storage.
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
    """
    Reference-counted lock entry.

    ``users`` includes both waiting threads and the thread currently
    holding/using the lock.

    This prevents the lock registry from growing forever while also
    preventing unsafe lock deletion while another thread can still use it.
    """

    lock: RLock
    users: int = 0


class Indexer:
    """
    Production document indexer.

    Guarantees:

        - Same-document operations are serialized.
        - Different documents may run concurrently.
        - Embeddings are generated before storage mutation.
        - Reindexing does not delete the previous version first.
        - Failed preparation preserves the previous document.
        - Document lock entries are cleaned up safely.
    """

    def __init__(
        self,
        *,
        chunker: DocumentChunker,
        embedding_provider: EmbeddingProvider,
        vector_store: VectorStore,
    ) -> None:
        self._chunker = chunker
        self._embedding_provider = embedding_provider
        self._vector_store = vector_store

        self._lock = RLock()
        self._document_locks: dict[
            str,
            _DocumentLockEntry,
        ] = {}

    @property
    def chunker(self) -> DocumentChunker:
        return self._chunker

    @property
    def embedding_provider(self) -> EmbeddingProvider:
        return self._embedding_provider

    @property
    def vector_store(self) -> VectorStore:
        return self._vector_store

    def index(
        self,
        document: Document,
    ) -> list[Chunk]:
        """
        Index a document.

        The complete chunk/embedding set is prepared before replacing
        the document in the vector store.
        """
        with self._document_lock(document.id):
            chunks = self._prepare_document(
                document
            )

            self._replace_document(
                document.id,
                chunks,
            )

            return [
                chunk
                for chunk, _ in chunks
            ]

    def index_many(
        self,
        documents: Iterable[Document],
    ) -> list[Chunk]:
        """
        Index multiple documents.

        Each document is synchronized independently.
        """
        indexed_chunks: list[Chunk] = []

        for document in documents:
            indexed_chunks.extend(
                self.index(document)
            )

        return indexed_chunks

    def remove(
        self,
        document_id: str,
    ) -> None:
        """
        Remove all indexed data belonging to a document.
        """
        self._validate_document_id(
            document_id
        )

        with self._document_lock(document_id):
            self._vector_store.delete_document(
                document_id
            )

    def reindex(
        self,
        document: Document,
    ) -> list[Chunk]:
        """
        Atomically replace the indexed version of a document.

        Critical failure guarantee:

            prepare
                â†“
            chunk
                â†“
            embed everything
                â†“
            replace

        If chunking or embedding fails, the previous version remains intact.
        """
        with self._document_lock(document.id):
            prepared = self._prepare_document(
                document
            )

            self._replace_document(
                document.id,
                prepared,
            )

            return [
                chunk
                for chunk, _ in prepared
            ]

    def _prepare_document(
        self,
        document: Document,
    ) -> list[tuple[Chunk, list[float]]]:
        """
        Prepare a complete document version without mutating storage.
        """
        chunks = self._chunker.chunk(
            document
        )

        prepared: list[
            tuple[Chunk, list[float]]
        ] = []

        seen_ids: set[str] = set()

        for chunk in chunks:
            if chunk.document_id != document.id:
                raise ValueError(
                    "Chunk document ID does not match "
                    f"document ID '{document.id}'."
                )

            if chunk.id in seen_ids:
                raise ValueError(
                    f"Duplicate chunk ID '{chunk.id}' "
                    "generated for document."
                )

            seen_ids.add(chunk.id)

            embedding = self._embedding_provider.embed(
                chunk.text
            )

            prepared.append(
                (
                    chunk,
                    [
                        float(value)
                        for value in embedding
                    ],
                )
            )

        return prepared

    def _replace_document(
        self,
        document_id: str,
        prepared: list[
            tuple[Chunk, list[float]]
        ],
    ) -> None:
        """
        Replace a document through the VectorStore's atomic replacement
        capability.
        """
        self._vector_store.replace_document(
            document_id,
            prepared,
        )

    @contextmanager
    def _document_lock(
        self,
        document_id: str,
    ) -> Iterator[None]:
        """
        Acquire the stable per-document lock.

        Registry references are incremented before the lock is acquired,
        meaning the entry cannot be removed while another thread is waiting
        for it.
        """
        self._validate_document_id(
            document_id
        )

        with self._lock:
            entry = self._document_locks.get(
                document_id
            )

            if entry is None:
                entry = _DocumentLockEntry(
                    lock=RLock()
                )

                self._document_locks[
                    document_id
                ] = entry

            entry.users += 1

        try:
            with entry.lock:
                yield

        finally:
            with self._lock:
                entry.users -= 1

                current = self._document_locks.get(
                    document_id
                )

                if (
                    current is entry
                    and entry.users == 0
                ):
                    del self._document_locks[
                        document_id
                    ]

    @staticmethod
    def _validate_document_id(
        document_id: str,
    ) -> None:
        if not isinstance(
            document_id,
            str,
        ):
            raise TypeError(
                "Document ID must be a string."
            )

        if not document_id.strip():
            raise ValueError(
                "Document ID cannot be empty."
            )
