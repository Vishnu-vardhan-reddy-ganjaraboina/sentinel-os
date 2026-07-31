"""
Metadata model for Sentinel capabilities.
"""

from __future__ import annotations

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
        """
        Validate metadata.
        """
        if not self.capability_id.strip():
            raise ValueError("capability_id cannot be empty.")

        if not self.name.strip():
            raise ValueError("name cannot be empty.")

        if not self.description.strip():
            raise ValueError("description cannot be empty.")

    def to_dict(self) -> dict[str, Any]:
        """
        Serialize metadata.
        """
        return {
            "capability_id": self.capability_id,
            "name": self.name,
            "description": self.description,
            "category": self.category.value,
            "version": self.version,
            "author": self.author,
            "enabled": self.enabled,
            "tags": self.tags,
            "permissions": self.permissions,
            "input_schema": self.input_schema,
            "output_schema": self.output_schema,
        }

    @classmethod
    def from_dict(
        cls,
        data: dict[str, Any],
    ) -> CapabilityMetadata:
        """
        Deserialize metadata.
        """
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
            tags=data.get("tags", []),
            permissions=data.get("permissions", []),
            input_schema=data.get("input_schema", {}),
            output_schema=data.get("output_schema", {}),
        )