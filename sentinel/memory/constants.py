"""
Constants for the Sentinel Memory subsystem.
"""

from enum import StrEnum

DEFAULT_MEMORY_VERSION = "1.0.0"

DEFAULT_IMPORTANCE = 1

DEFAULT_TTL = None


class MemoryType(StrEnum):
    """
    Supported memory categories.
    """

    WORKING = "working"
    SHORT_TERM = "short_term"
    LONG_TERM = "long_term"
    EPISODIC = "episodic"
    SEMANTIC = "semantic"


class MemoryStatus(StrEnum):
    """
    Status of a memory entry.
    """

    ACTIVE = "active"
    ARCHIVED = "archived"
    EXPIRED = "expired"
    DELETED = "deleted"