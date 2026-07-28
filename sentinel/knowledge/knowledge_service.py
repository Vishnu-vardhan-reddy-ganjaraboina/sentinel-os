"""
Knowledge service.

Provides the public API for Sentinel's knowledge subsystem.
"""

from __future__ import annotations

from collections.abc import Iterable

from sentinel.knowledge.chunk import Chunk
from sentinel.knowledge.document import Document
from sentinel.knowledge.indexer import Indexer
from sentinel.knowledge.retriever import Retriever


class KnowledgeService:
    """
    High-level interface to the knowledge subsystem.

    Coordinates indexing and retrieval while hiding
    implementation details from callers.
    """

    def __init__(
        self,
        *,
        indexer: Indexer,
        retriever: Retriever,
    ) -> None:
        self._indexer = indexer
        self._retriever = retriever

    @property
    def indexer(self) -> Indexer:
        return self._indexer

    @property
    def retriever(self) -> Retriever:
        return self._retriever

    def add_document(
        self,
        document: Document,
    ) -> list[Chunk]:
        """
        Index a single document.
        """
        return self._indexer.index(document)

    def add_documents(
        self,
        documents: Iterable[Document],
    ) -> list[Chunk]:
        """
        Index multiple documents.
        """
        return self._indexer.index_many(documents)

    def remove_document(
        self,
        document_id: str,
    ) -> None:
        """
        Remove a document from the knowledge base.
        """
        self._indexer.remove(document_id)

    def reindex_document(
        self,
        document: Document,
    ) -> list[Chunk]:
        """
        Replace an indexed document.
        """
        return self._indexer.reindex(document)

    def search(
        self,
        query: str,
        *,
        limit: int = 5,
    ) -> list[Chunk]:
        """
        Search indexed knowledge.
        """
        return self._retriever.retrieve(
            query,
            limit=limit,
        )