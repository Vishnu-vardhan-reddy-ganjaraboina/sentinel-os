"""
Results returned by Sentinel boot operations.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from collections.abc import Mapping
from typing import Any


@dataclass(frozen=True, slots=True)
class BootResult:
    """
    Immutable result describing a boot operation.
    """

    success: bool
    profile: str
    message: str
    details: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.success, bool):
            raise TypeError("success must be a boolean.")

        if not isinstance(self.profile, str):
            raise TypeError("profile must be a string.")

        profile = self.profile.strip()
        if not profile:
            raise ValueError("profile cannot be empty.")

        if not isinstance(self.message, str):
            raise TypeError("message must be a string.")

        if not isinstance(self.details, Mapping):
            raise TypeError("details must be a mapping.")

        object.__setattr__(
            self,
            "profile",
            profile,
        )
        object.__setattr__(
            self,
            "details",
            MappingProxyType(dict(self.details)),
        )

    def to_dict(self) -> dict[str, Any]:
        """Return an isolated dictionary representation."""
        return {
            "success": self.success,
            "profile": self.profile,
            "message": self.message,
            "details": dict(self.details),
        }
