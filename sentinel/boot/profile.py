"""
Boot configuration profile for Sentinel OS.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from collections.abc import Mapping
from typing import Any


@dataclass(frozen=True, slots=True)
class BootProfile:
    """
    Immutable configuration describing how Sentinel should boot.

    The initial profile intentionally stays small. More boot options can
    be added later without changing the BootManager lifecycle contract.
    """

    name: str = "default"
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.name, str):
            raise TypeError("name must be a string.")

        name = self.name.strip()
        if not name:
            raise ValueError("name cannot be empty.")

        if not isinstance(self.metadata, Mapping):
            raise TypeError("metadata must be a mapping.")

        object.__setattr__(
            self,
            "name",
            name,
        )
        object.__setattr__(
            self,
            "metadata",
            MappingProxyType(dict(self.metadata)),
        )

    def to_dict(self) -> dict[str, Any]:
        """Return an isolated dictionary representation."""
        return {
            "name": self.name,
            "metadata": dict(self.metadata),
        }

    def __repr__(self) -> str:
        return (
            "BootProfile("
            f"name={self.name!r}, "
            f"metadata={dict(self.metadata)!r}"
            ")"
        )
