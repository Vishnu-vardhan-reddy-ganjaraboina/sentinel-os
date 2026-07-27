"""
Knowledge interfaces for Sentinel OS.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Iterable

from sentinel.knowledge.document import Document


class KnowledgeProvider(ABC):
    """
    Base interface for all knowledge providers.
    """

    @abstractmethod
    def add(
        self,
        document: Document,
    ) -> None:
        """
        Add a document.
        """
        raise NotImplementedError

    @abstractmethod
    def get(
        self,
        document_id: str,
    ) -> Document:
        """
        Retrieve a document.
        """
        raise NotImplementedError

    @abstractmethod
    def delete(
        self,
        document_id: str,
    ) -> None:
        """
        Remove a document.
        """
        raise NotImplementedError

    @abstractmethod
    def search(
        self,
        query: str,
    ) -> Iterable[Document]:
        """
        Search for matching documents.
        """
        raise NotImplementedError
