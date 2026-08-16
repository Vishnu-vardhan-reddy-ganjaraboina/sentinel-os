"""
Knowledge layer for Sentinel OS.
"""

from sentinel.knowledge.chunk import Chunk
from sentinel.knowledge.document import Document
from sentinel.knowledge.embeddings import (
    DummyEmbeddingProvider,
    EmbeddingProvider,
)
from sentinel.knowledge.knowledge_base import KnowledgeBase
from sentinel.knowledge.knowledge_service import KnowledgeService
from sentinel.knowledge.retriever import Retriever
from sentinel.knowledge.runtime import KnowledgeRuntimeService
from sentinel.knowledge.vector_store import (
    InMemoryVectorStore,
    VectorStore,
)

__all__ = [
    "Chunk",
    "Document",
    "EmbeddingProvider",
    "DummyEmbeddingProvider",
    "VectorStore",
    "InMemoryVectorStore",
    "Retriever",
    "KnowledgeBase",
    "KnowledgeService",
    "KnowledgeRuntimeService",
]