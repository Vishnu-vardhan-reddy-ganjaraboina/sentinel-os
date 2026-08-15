"""
Kernel runtime service for the Sentinel Knowledge subsystem.
"""

from __future__ import annotations

from sentinel.kernel.service import Service
from sentinel.knowledge.chunker import FixedSizeChunker
from sentinel.knowledge.embeddings import DummyEmbeddingProvider
from sentinel.knowledge.indexer import Indexer
from sentinel.knowledge.knowledge_service import KnowledgeService
from sentinel.knowledge.retriever import Retriever
from sentinel.knowledge.vector_store import InMemoryVectorStore


class KnowledgeRuntimeService(Service):
    """
    Kernel-managed runtime wrapper for KnowledgeService.
    """

    def __init__(
        self,
        knowledge: KnowledgeService | None = None,
    ) -> None:
        super().__init__("knowledge")

        self._knowledge = (
            knowledge
            if knowledge is not None
            else self._create_default_service()
        )

    @staticmethod
    def _create_default_service() -> KnowledgeService:
        """
        Create the default in-memory knowledge service.
        """
        embedding_provider = DummyEmbeddingProvider()
        vector_store = InMemoryVectorStore()

        indexer = Indexer(
            chunker=FixedSizeChunker(),
            embedding_provider=embedding_provider,
            vector_store=vector_store,
        )

        retriever = Retriever(
            embedding_provider=embedding_provider,
            vector_store=vector_store,
        )

        return KnowledgeService(
            indexer=indexer,
            retriever=retriever,
        )

    @property
    def knowledge(self) -> KnowledgeService:
        """Return the underlying knowledge service."""
        return self._knowledge

    def initialize(self) -> None:
        """
        Initialize knowledge resources.

        The current knowledge implementation creates its resources
        during construction, so no additional initialization is required.
        """

    def shutdown(self) -> None:
        """
        Shut down knowledge resources.

        The current knowledge implementation uses in-memory storage,
        so there are no external resources requiring explicit shutdown.
        """

    def health(self) -> dict[str, bool]:
        """Return knowledge service health information."""
        return {
            "healthy": True,
        }
