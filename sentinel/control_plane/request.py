from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

from sentinel.control_plane.commands import KernelCommand
from sentinel.control_plane.context import ControlContext


@dataclass(frozen=True, slots=True)
class ControlRequest:
    """
    Structured request submitted to the Sentinel Control Plane.

    The request contains the command, caller context, and command data.
    Command-specific validation is handled separately.
    """

    command: KernelCommand
    context: ControlContext
    data: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.command, KernelCommand):
            raise TypeError(
                "command must be a KernelCommand."
            )

        if not isinstance(self.context, ControlContext):
            raise TypeError(
                "context must be a ControlContext."
            )

        object.__setattr__(
            self,
            "data",
            dict(self.data),
        )