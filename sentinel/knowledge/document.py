"""
Document model for Sentinel OS.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class Document:
    """
    Represents a knowledge document.
    """

    id: str
    text: str
    metadata: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValueError("Document id cannot be empty.")

        if not self.text.strip():
            raise ValueError("Document text cannot be empty.")