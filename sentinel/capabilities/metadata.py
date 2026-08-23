"""
Metadata model for Sentinel capabilities.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any

from sentinel.capabilities.constants import (
    DEFAULT_CAPABILITY_VERSION,
    CapabilityCategory,
)


@dataclass(slots=True)
class CapabilityMetadata:
    """
    Describes a capability.

    This metadata is used for discovery, registration,
    documentation, validation, and runtime inspection.
    """

    capability_id: str

    name: str

    description: str

    category: CapabilityCategory

    version: str = DEFAULT_CAPABILITY_VERSION

    author: str = ""

    enabled: bool = True

    tags: list[str] = field(default_factory=list)

    permissions: list[str] = field(default_factory=list)

    input_schema: dict[str, Any] = field(default_factory=dict)

    output_schema: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate metadata."""
        if not isinstance(self.capability_id, str):
            raise TypeError("capability_id must be a string.")

        if not self.capability_id.strip():
            raise ValueError("capability_id cannot be empty.")

        if not isinstance(self.name, str):
            raise TypeError("name must be a string.")

        if not self.name.strip():
            raise ValueError("name cannot be empty.")

        if not isinstance(self.description, str):
            raise TypeError("description must be a string.")

        if not self.description.strip():
            raise ValueError("description cannot be empty.")

        if not isinstance(self.category, CapabilityCategory):
            raise TypeError(
                "category must be a CapabilityCategory."
            )

        if not isinstance(self.version, str):
            raise TypeError("version must be a string.")

        if not self.version.strip():
            raise ValueError("version cannot be empty.")

        if not isinstance(self.author, str):
            raise TypeError("author must be a string.")

        if not isinstance(self.enabled, bool):
            raise TypeError("enabled must be a boolean.")

        if not isinstance(self.tags, list):
            raise TypeError("tags must be a list.")

        if not all(isinstance(tag, str) for tag in self.tags):
            raise TypeError("all tags must be strings.")

        if not isinstance(self.permissions, list):
            raise TypeError("permissions must be a list.")

        if not all(
            isinstance(permission, str)
            for permission in self.permissions
        ):
            raise TypeError(
                "all permissions must be strings."
            )

        if not isinstance(self.input_schema, dict):
            raise TypeError(
                "input_schema must be a dictionary."
            )

        if not isinstance(self.output_schema, dict):
            raise TypeError(
                "output_schema must be a dictionary."
            )

    def to_dict(self) -> dict[str, Any]:
        """
        Serialize metadata.

        Returned mutable structures are deep copies so callers
        cannot mutate the metadata object accidentally.
        """
        return {
            "capability_id": self.capability_id,
            "name": self.name,
            "description": self.description,
            "category": self.category.value,
            "version": self.version,
            "author": self.author,
            "enabled": self.enabled,
            "tags": deepcopy(self.tags),
            "permissions": deepcopy(self.permissions),
            "input_schema": deepcopy(self.input_schema),
            "output_schema": deepcopy(self.output_schema),
        }

    @classmethod
    def from_dict(
        cls,
        data: dict[str, Any],
    ) -> CapabilityMetadata:
        """
        Deserialize metadata.
        """
        if not isinstance(data, dict):
            raise TypeError("metadata data must be a dictionary.")

        return cls(
            capability_id=data["capability_id"],
            name=data["name"],
            description=data["description"],
            category=CapabilityCategory(data["category"]),
            version=data.get(
                "version",
                DEFAULT_CAPABILITY_VERSION,
            ),
            author=data.get("author", ""),
            enabled=data.get("enabled", True),
            tags=deepcopy(data.get("tags", [])),
            permissions=deepcopy(data.get("permissions", [])),
            input_schema=deepcopy(
                data.get("input_schema", {})
            ),
            output_schema=deepcopy(
                data.get("output_schema", {})
            ),
        )