"""
Document chunking for Sentinel OS.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from sentinel.knowledge.chunk import Chunk
from sentinel.knowledge.constants import (
    DEFAULT_CHUNK_OVERLAP,
    DEFAULT_CHUNK_SIZE,
)
from sentinel.knowledge.document import Document


class DocumentChunker(ABC):
    """
    Base interface for document chunkers.
    """

    @abstractmethod
    def chunk(
        self,
        document: Document,
    ) -> list[Chunk]:
        """
        Split a document into chunks.
        """
        raise NotImplementedError


class FixedSizeChunker(DocumentChunker):
    """
    Splits documents into fixed-size chunks with optional overlap.
    """

    def __init__(
        self,
        *,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        overlap: int = DEFAULT_CHUNK_OVERLAP,
    ) -> None:
        if chunk_size <= 0:
            raise ValueError("chunk_size must be greater than zero.")

        if overlap < 0:
            raise ValueError("overlap cannot be negative.")

        if overlap >= chunk_size:
            raise ValueError(
                "overlap must be smaller than chunk_size."
            )

        self._chunk_size = chunk_size
        self._overlap = overlap

    @property
    def chunk_size(self) -> int:
        return self._chunk_size

    @property
    def overlap(self) -> int:
        return self._overlap

    def chunk(
        self,
        document: Document,
    ) -> list[Chunk]:
        """
        Split a document into fixed-size chunks.
        """
        text = document.text

        if len(text) <= self._chunk_size:
            return [
                Chunk(
                    id=f"{document.id}:0",
                    document_id=document.id,
                    text=text,
                    index=0,
                    metadata=document.metadata.copy(),
                )
            ]

        chunks: list[Chunk] = []

        start = 0
        index = 0

        while start < len(text):
            end = start + self._chunk_size

            chunks.append(
                Chunk(
                    id=f"{document.id}:{index}",
                    document_id=document.id,
                    text=text[start:end],
                    index=index,
                    metadata=document.metadata.copy(),
                )
            )

            if end >= len(text):
                break

            start = end - self._overlap
            index += 1

        return chunks