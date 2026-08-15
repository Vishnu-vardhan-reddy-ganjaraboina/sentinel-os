"""
Constants for the Sentinel Memory subsystem.
"""

from __future__ import annotations

from datetime import timedelta
from enum import StrEnum

DEFAULT_MEMORY_VERSION = "1.0.0"

DEFAULT_IMPORTANCE = 1

DEFAULT_TTL: timedelta | None = None


class MemoryType(StrEnum):
    """
    Types of memory stored by Sentinel.
    """

    WORKING = "working"
    SHORT_TERM = "short_term"
    LONG_TERM = "long_term"
    EPISODIC = "episodic"
    SEMANTIC = "semantic"


class MemoryStatus(StrEnum):
    """
    Lifecycle states for a memory entry.
    """

    ACTIVE = "active"
    ARCHIVED = "archived"
    DELETED = "deleted"
