"""
Result model for Sentinel Kernel Control Plane operations.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class ControlResult:
    """Represent the result of a Kernel Control Plane operation."""

    success: bool
    command: str
    data: Mapping[str, Any] = field(default_factory=dict)
    error: str | None = None