"""
Immutable event object for Sentinel OS.

Events represent things that have already happened.

Examples:
    - ServiceStarted
    - ServiceStopped
    - KernelBooted
    - MemoryLoaded
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from collections.abc import Mapping
from typing import Any


@dataclass(frozen=True, slots=True)
class Event:
    """
    Immutable event.

    Attributes
    ----------
    name:
        Event type.

    source:
        Service that produced the event.

    payload:
        Additional event information.

    timestamp:
        UTC creation time.
    """

    name: str

    source: str

    payload: Mapping[str, Any] = field(default_factory=dict)

    timestamp: datetime = field(
        default_factory=lambda: datetime.now(UTC)
    )

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError(
                "Event name cannot be empty."
            )

        if not self.source.strip():
            raise ValueError(
                "Event source cannot be empty."
            )