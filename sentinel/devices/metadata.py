"""
Metadata model for Sentinel devices.
"""

from __future__ import annotations

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
        if not self.device_id.strip():
            raise ValueError("device_id cannot be empty.")

        if not self.name.strip():
            raise ValueError("name cannot be empty.")

        if not self.description.strip():
            raise ValueError("description cannot be empty.")

    def to_dict(self) -> dict[str, Any]:
        """
        Serialize metadata.
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
            "capabilities": self.capabilities,
            "properties": self.properties,
        }

    @classmethod
    def from_dict(
        cls,
        data: dict[str, Any],
    ) -> "DeviceMetadata":
        """
        Deserialize metadata.
        """
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
            capabilities=data.get("capabilities", []),
            properties=data.get("properties", {}),
        )