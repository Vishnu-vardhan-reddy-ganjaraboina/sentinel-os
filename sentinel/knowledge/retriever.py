"""
Retriever implementation for Sentinel OS.
"""

from __future__ import annotations

from sentinel.knowledge.chunk import Chunk
from sentinel.knowledge.embeddings import EmbeddingProvider
from sentinel.knowledge.vector_store import VectorStore


class Retriever:
    """
    Retrieves relevant chunks using embeddings.
    """

    def __init__(
        self,
        embedding_provider: EmbeddingProvider,
        vector_store: VectorStore,
    ) -> None:
        self._embedding_provider = embedding_provider
        self._vector_store = vector_store

    def retrieve(
        self,
        query: str,
        *,
        limit: int = 5,
    ) -> list[Chunk]:
        """
        Retrieve the most relevant chunks.
        """
        embedding = self._embedding_provider.embed(query)

        return self._vector_store.search(
            embedding,
            limit=limit,
        )