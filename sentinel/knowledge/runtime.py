"""
Kernel runtime service for the Sentinel Knowledge subsystem.
"""

from __future__ import annotations

from sentinel.kernel.service import Service
from sentinel.knowledge.chunker import DocumentChunker, FixedSizeChunker
from sentinel.knowledge.embeddings import (
    DummyEmbeddingProvider,
    EmbeddingProvider,
)
from sentinel.knowledge.indexer import Indexer
from sentinel.knowledge.knowledge_service import KnowledgeService
from sentinel.knowledge.retriever import Retriever
from sentinel.knowledge.vector_store import (
    InMemoryVectorStore,
    VectorStore,
)


class KnowledgeRuntimeService(Service):
    """
    Kernel-managed runtime wrapper for KnowledgeService.

    Dependencies are injected so the runtime can use different
    embedding providers, chunkers, and vector stores in different
    deployments.
    """

    def __init__(
        self,
        knowledge: KnowledgeService | None = None,
        *,
        embedding_provider: EmbeddingProvider | None = None,
        vector_store: VectorStore | None = None,
        chunker: DocumentChunker | None = None,
    ) -> None:
        super().__init__("knowledge")

        self._knowledge = (
            knowledge
            if knowledge is not None
            else self._create_default_service(
                embedding_provider=embedding_provider,
                vector_store=vector_store,
                chunker=chunker,
            )
        )

    @staticmethod
    def _create_default_service(
        *,
        embedding_provider: EmbeddingProvider | None = None,
        vector_store: VectorStore | None = None,
        chunker: DocumentChunker | None = None,
    ) -> KnowledgeService:
        """
        Create the default knowledge service.

        Defaults remain deterministic and in-memory, making the runtime
        suitable for tests and lightweight deployments while allowing
        production implementations to be injected.
        """
        provider = (
            embedding_provider
            if embedding_provider is not None
            else DummyEmbeddingProvider()
        )

        store = (
            vector_store
            if vector_store is not None
            else InMemoryVectorStore()
        )

        document_chunker = (
            chunker
            if chunker is not None
            else FixedSizeChunker()
        )

        indexer = Indexer(
            chunker=document_chunker,
            embedding_provider=provider,
            vector_store=store,
        )

        retriever = Retriever(
            embedding_provider=provider,
            vector_store=store,
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

        The current vector-store implementations initialize during
        construction, so no additional initialization is required.
        """

    def shutdown(self) -> None:
        """
        Shut down knowledge resources.

        Resource-owning implementations can expose lifecycle behavior
        through the service in future deployments.
        """

    def health(self) -> dict[str, bool]:
        """Return knowledge service health information."""
        return {
            "healthy": True,
        }