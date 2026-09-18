"""
Request model for the Sentinel Kernel Control Plane.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from sentinel.control_plane.commands import KernelCommand
from sentinel.control_plane.context import ControlContext


@dataclass(frozen=True, slots=True)
class ControlRequest:
    """Represent a complete Kernel Control Plane request."""

    command: KernelCommand
    context: ControlContext
    data: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "data", dict(self.data))