"""
Caller context for the Sentinel Kernel Control Plane.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class ControlContext:
    """
    Describe the caller making a Control Plane request.

    Identity and authorization are intentionally separate concerns.
    """

    caller_id: str
    caller_type: str
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.caller_id.strip():
            raise ValueError("caller_id must not be empty.")

        if not self.caller_type.strip():
            raise ValueError("caller_type must not be empty.")

        object.__setattr__(self, "metadata", dict(self.metadata))