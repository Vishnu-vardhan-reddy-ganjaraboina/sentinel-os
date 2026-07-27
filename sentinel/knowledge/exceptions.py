"""
Knowledge exceptions for Sentinel OS.
"""

from __future__ import annotations

from sentinel.core.exceptions import SentinelError


class KnowledgeError(SentinelError):
    """
    Base exception for knowledge layer.
    """


class DocumentNotFoundError(KnowledgeError):
    """
    Raised when a document cannot be found.
    """


class ChunkNotFoundError(KnowledgeError):
    """
    Raised when a chunk cannot be found.
    """


class EmbeddingError(KnowledgeError):
    """
    Raised when embedding generation fails.
    """


class VectorStoreError(KnowledgeError):
    """
    Raised when vector store operations fail.
    """


class RetrievalError(KnowledgeError):
    """
    Raised when retrieval fails.
    """