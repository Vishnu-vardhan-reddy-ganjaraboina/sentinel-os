"""
Indexer implementation.

The Indexer is responsible for transforming documents into searchable
knowledge by coordinating chunking, embedding generation, and vector
storage.

Pipeline:

Document
    ↓
Chunker
    ↓
Chunks
    ↓
Embedding Provider
    ↓
Embeddings
    ↓
Vector Store
"""

from __future__ import annotations

from collections.abc import Iterable

from sentinel.knowledge.chunk import Chunk
from sentinel.knowledge.chunker import DocumentChunker
from sentinel.knowledge.document import Document
from sentinel.knowledge.embeddings import EmbeddingProvider
from sentinel.knowledge.vector_store import VectorStore


class Indexer:
    """
    Coordinates document indexing.

    The Indexer is intentionally stateless. It orchestrates the indexing
    pipeline but owns no persistent data itself.
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
        """
        Index a single document.

        Parameters
        ----------
        document:
            Document to index.

        Returns
        -------
        list[Chunk]
            Generated chunks.
        """
        chunks = self._chunker.chunk(document)

        for chunk in chunks:
            embedding = self._embedding_provider.embed(chunk.text)
            self._vector_store.add(chunk, embedding)

        return chunks

    def index_many(self, documents: Iterable[Document]) -> list[Chunk]:
        """
        Index multiple documents.

        Returns every generated chunk.
        """
        indexed_chunks: list[Chunk] = []

        for document in documents:
            indexed_chunks.extend(self.index(document))

        return indexed_chunks

    def remove(
        self,
        document_id: str,
    ) -> None:
       """
        Remove every indexed chunk belonging to a document.
        """
       self._vector_store.delete_document(document_id)

    def reindex(
        self,
        document: Document,
    ) -> list[Chunk]:
        """
        Replace existing indexed data for a document.
        """
        self.remove(document.id)
        return self.index(document)