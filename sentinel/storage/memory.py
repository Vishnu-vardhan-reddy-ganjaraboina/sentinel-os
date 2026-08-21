"""
Public in-memory storage API for Sentinel OS.
"""

from __future__ import annotations

from sentinel.storage.backends.in_memory import MemoryBackend


class MemoryStorage(MemoryBackend):
    """
    Public in-memory storage implementation.

    This class intentionally provides the stable public API while
    delegating implementation to MemoryBackend.
    """