"""
Knowledge chunk model.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class Chunk:
    """
    Represents a chunk of a document.
    """

    id: str
    document_id: str
    text: str
    index: int
    metadata: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValueError("Chunk id cannot be empty.")

        if not self.document_id.strip():
            raise ValueError("Document id cannot be empty.")

        if not self.text.strip():
            raise ValueError("Chunk text cannot be empty.")

        if self.index < 0:
            raise ValueError("Chunk index must be non-negative.")