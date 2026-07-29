"""
High-level service for the Sentinel Devices subsystem.
"""

from __future__ import annotations

from typing import Any

from sentinel.devices.device import BaseDevice
from sentinel.devices.manager import DeviceManager
from sentinel.devices.registry import DeviceRegistry


class DeviceService:
    """
    Public API for interacting with Sentinel devices.

    The service delegates device management and execution to the
    underlying DeviceManager while providing a stable interface for
    other Sentinel subsystems.
    """

    def __init__(
        self,
        manager: DeviceManager | None = None,
    ) -> None:
        self._manager = manager or DeviceManager()

    @property
    def manager(self) -> DeviceManager:
        """
        Return the underlying device manager.
        """
        return self._manager

    @property
    def registry(self) -> DeviceRegistry:
        """
        Return the underlying device registry.
        """
        return self._manager.registry

    def register(
        self,
        device: BaseDevice,
    ) -> None:
        """
        Register a device.
        """
        self._manager.register(device)

    def unregister(
        self,
        device_id: str,
    ) -> None:
        """
        Unregister a device.
        """
        self._manager.unregister(device_id)

    def connect(
        self,
        device_id: str,
    ) -> None:
        """
        Connect a registered device.
        """
        self._manager.connect(device_id)

    def disconnect(
        self,
        device_id: str,
    ) -> None:
        """
        Disconnect a registered device.
        """
        self._manager.disconnect(device_id)

    def execute(
        self,
        device_id: str,
        **kwargs: Any,
    ) -> Any:
        """
        Execute a device operation.
        """
        return self._manager.execute(
            device_id,
            **kwargs,
        )

    def exists(
        self,
        device_id: str,
    ) -> bool:
        """
        Return True if the device exists.
        """
        return self._manager.exists(device_id)

    def list(self) -> list[BaseDevice]:
        """
        Return all registered devices.
        """
        return self._manager.list()

    def clear(self) -> None:
        """
        Remove all registered devices.
        """
        self._manager.clear()