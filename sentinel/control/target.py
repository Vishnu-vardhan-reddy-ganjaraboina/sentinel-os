"""
Protocol for objects controlled by the Sentinel local control server.
"""

from __future__ import annotations

from collections.abc import Mapping
from enum import Enum
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class ProcessControlTarget(Protocol):
    """Interface required by the local control server."""

    @property
    def state(self) -> Enum:
        """Return the current process state."""
        ...

    @property
    def running(self) -> bool:
        """Return whether the process is running."""
        ...

    def request_stop(self) -> None:
        """Request process shutdown."""
        ...

    def health(self) -> Mapping[str, Any]:
        """Return process health."""
        ...
