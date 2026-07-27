"""
Knowledge base implementation for Sentinel OS.
"""

from __future__ import annotations

from sentinel.knowledge.chunk import Chunk
from sentinel.knowledge.document import Document
from sentinel.knowledge.embeddings import EmbeddingProvider
from sentinel.knowledge.retriever import Retriever
from sentinel.knowledge.vector_store import VectorStore


class KnowledgeBase:
    """
    Coordinates storage and retrieval of knowledge.
    """

    def __init__(
        self,
        embedding_provider: EmbeddingProvider,
        vector_store: VectorStore,
    ) -> None:
        self._embedding_provider = embedding_provider
        self._vector_store = vector_store
        self._retriever = Retriever(
            embedding_provider,
            vector_store,
        )

    def add_document(
        self,
        document: Document,
    ) -> None:
        """
        Add a document to the knowledge base.

        For now, each document becomes one chunk.
        """
        chunk = Chunk(
            id=document.id,
            document_id=document.id,
            text=document.text,
            index=0,
            metadata=document.metadata.copy(),
        )

        embedding = self._embedding_provider.embed(
            chunk.text
        )

        self._vector_store.add(
            chunk,
            embedding,
        )

    def search(
        self,
        query: str,
        *,
        limit: int = 5,
    ) -> list[Chunk]:
        """
        Search the knowledge base.
        """
        return self._retriever.retrieve(
            query,
            limit=limit,
        )