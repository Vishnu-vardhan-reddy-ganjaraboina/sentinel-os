"""
sentinel.knowledge.exceptions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Exception hierarchy for the Knowledge subsystem.

The Knowledge subsystem exposes a well-defined set of domain-specific
exceptions. Higher-level subsystems should catch KnowledgeError unless
they need to handle a more specific condition.

RFC:
    RFC-0003 Knowledge Subsystem
"""

from __future__ import annotations

__all__ = [
    "SentinelError",
    "KnowledgeError",
    "ValidationError",
    "InvalidKnowledgeError",
    "InvalidIdentifierError",
    "InvalidRelationshipError",
    "NotFoundError",
    "KnowledgeNotFoundError",
    "ConflictError",
    "DuplicateKnowledgeError",
    "StorageError",
]


class SentinelError(Exception):
    """
    Base exception for all Sentinel OS subsystems.
    """


class KnowledgeError(SentinelError):
    """
    Base exception for all Knowledge subsystem errors.
    """


class ValidationError(KnowledgeError):
    """
    Raised when domain validation fails.
    """


class InvalidKnowledgeError(ValidationError):
    """
    Raised when a KnowledgeEntity contains invalid data.
    """


class InvalidIdentifierError(ValidationError):
    """
    Raised when an entity identifier is malformed or invalid.
    """


class InvalidRelationshipError(ValidationError):
    """
    Raised when a relationship definition is invalid.
    """


class NotFoundError(KnowledgeError):
    """
    Raised when a requested resource cannot be found.
    """


class KnowledgeNotFoundError(NotFoundError):
    """
    Raised when a knowledge entity cannot be located.
    """


class ConflictError(KnowledgeError):
    """
    Raised when an operation would violate uniqueness or consistency.
    """


class DuplicateKnowledgeError(ConflictError):
    """
    Raised when attempting to create a duplicate knowledge entity.
    """


class StorageError(KnowledgeError):
    """
    Raised when an underlying storage operation fails.
    """