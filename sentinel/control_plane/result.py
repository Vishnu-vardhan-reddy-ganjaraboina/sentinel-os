"""
Result model for Sentinel Kernel Control Plane operations.
"""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class ControlResult:
    """Represent the result of a Kernel Control Plane operation."""

    success: bool
    command: str
    data: Mapping[str, Any] = field(default_factory=dict)
    error: str | None = None
    audit_error: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "data", deepcopy(self.data))
