"""
Metadata model for Sentinel devices.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any

from sentinel.devices.constants import (
    DEFAULT_DEVICE_VERSION,
    DeviceCategory,
)


@dataclass(slots=True)
class DeviceMetadata:
    """
    Describes a device.

    This metadata is used for discovery, registration,
    monitoring, and runtime inspection.
    """

    device_id: str

    name: str

    description: str

    category: DeviceCategory

    version: str = DEFAULT_DEVICE_VERSION

    manufacturer: str = ""

    model: str = ""

    serial_number: str = ""

    connected: bool = False

    capabilities: list[str] = field(default_factory=list)

    properties: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate device metadata."""
        if not isinstance(self.device_id, str):
            raise TypeError("device_id must be a string.")

        if not self.device_id.strip():
            raise ValueError("device_id cannot be empty.")

        if not isinstance(self.name, str):
            raise TypeError("name must be a string.")

        if not self.name.strip():
            raise ValueError("name cannot be empty.")

        if not isinstance(self.description, str):
            raise TypeError("description must be a string.")

        if not self.description.strip():
            raise ValueError("description cannot be empty.")

        if not isinstance(self.category, DeviceCategory):
            raise TypeError(
                "category must be a DeviceCategory."
            )

        if not isinstance(self.version, str):
            raise TypeError("version must be a string.")

        if not self.version.strip():
            raise ValueError("version cannot be empty.")

        if not isinstance(self.manufacturer, str):
            raise TypeError("manufacturer must be a string.")

        if not isinstance(self.model, str):
            raise TypeError("model must be a string.")

        if not isinstance(self.serial_number, str):
            raise TypeError("serial_number must be a string.")

        if not isinstance(self.connected, bool):
            raise TypeError("connected must be a boolean.")

        if not isinstance(self.capabilities, list):
            raise TypeError("capabilities must be a list.")

        if not all(
            isinstance(capability, str)
            for capability in self.capabilities
        ):
            raise TypeError(
                "all capabilities must be strings."
            )

        if not isinstance(self.properties, dict):
            raise TypeError("properties must be a dictionary.")

    def to_dict(self) -> dict[str, Any]:
        """
        Serialize metadata.

        Mutable structures are copied so callers cannot mutate
        the metadata object through the serialized representation.
        """
        return {
            "device_id": self.device_id,
            "name": self.name,
            "description": self.description,
            "category": self.category.value,
            "version": self.version,
            "manufacturer": self.manufacturer,
            "model": self.model,
            "serial_number": self.serial_number,
            "connected": self.connected,
            "capabilities": deepcopy(self.capabilities),
            "properties": deepcopy(self.properties),
        }

    @classmethod
    def from_dict(
        cls,
        data: dict[str, Any],
    ) -> DeviceMetadata:
        """
        Deserialize metadata.
        """
        if not isinstance(data, dict):
            raise TypeError("metadata data must be a dictionary.")

        return cls(
            device_id=data["device_id"],
            name=data["name"],
            description=data["description"],
            category=DeviceCategory(data["category"]),
            version=data.get(
                "version",
                DEFAULT_DEVICE_VERSION,
            ),
            manufacturer=data.get("manufacturer", ""),
            model=data.get("model", ""),
            serial_number=data.get("serial_number", ""),
            connected=data.get("connected", False),
            capabilities=deepcopy(
                data.get("capabilities", [])
            ),
            properties=deepcopy(
                data.get("properties", {})
            ),
        )