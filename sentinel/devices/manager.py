"""
Device manager for the Sentinel Devices subsystem.
"""

from __future__ import annotations

from typing import Any

from sentinel.devices.device import BaseDevice
from sentinel.devices.exceptions import (
    DeviceDisconnectedError,
    DeviceOperationError,
)
from sentinel.devices.registry import DeviceRegistry


class DeviceManager:
    """
    Manages Sentinel devices.

    The manager acts as the runtime layer between the registry
    and the rest of Sentinel OS.
    """

    def __init__(
        self,
        registry: DeviceRegistry | None = None,
    ) -> None:
        self._registry = registry or DeviceRegistry()

    @property
    def registry(self) -> DeviceRegistry:
        """Return the device registry."""
        return self._registry

    def register(
        self,
        device: BaseDevice,
    ) -> None:
        """Register a device."""
        self._registry.register(device)

    def unregister(
        self,
        device_id: str,
    ) -> None:
        """Unregister a device."""
        self._registry.unregister(device_id)

    def connect(
        self,
        device_id: str,
    ) -> None:
        """Connect a registered device."""
        self._registry.get(device_id).connect()

    def disconnect(
        self,
        device_id: str,
    ) -> None:
        """Disconnect a registered device."""
        self._registry.get(device_id).disconnect()

    def execute(
        self,
        device_id: str,
        **kwargs: Any,
    ) -> Any:
        """
        Execute a device operation.

        Disconnection is a specific device state and is therefore
        preserved for callers. Other runtime failures are wrapped
        as DeviceOperationError.
        """
        device = self._registry.get(device_id)

        try:
            return device.execute(**kwargs)

        except DeviceDisconnectedError:
            raise

        except Exception as exc:
            raise DeviceOperationError(
                f"Device '{device_id}' operation failed."
            ) from exc

    def list(self) -> list[BaseDevice]:
        """Return all registered devices."""
        return self._registry.list()

    def exists(
        self,
        device_id: str,
    ) -> bool:
        """Return True if the device exists."""
        return self._registry.exists(device_id)

    def clear(self) -> None:
        """Remove all registered devices."""
        self._registry.clear()