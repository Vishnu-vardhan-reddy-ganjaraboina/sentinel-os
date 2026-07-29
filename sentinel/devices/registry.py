"""
Device registry for the Sentinel Devices subsystem.
"""

from __future__ import annotations

from threading import RLock

from sentinel.devices.constants import DeviceCategory
from sentinel.devices.device import BaseDevice
from sentinel.devices.exceptions import (
    DeviceAlreadyExistsError,
    DeviceNotFoundError,
)


class DeviceRegistry:
    """
    Thread-safe registry for Sentinel devices.
    """

    def __init__(self) -> None:
        self._devices: dict[str, BaseDevice] = {}
        self._lock = RLock()

    def register(
        self,
        device: BaseDevice,
    ) -> None:
        """
        Register a device.
        """
        with self._lock:
            if device.id in self._devices:
                raise DeviceAlreadyExistsError(
                    f"Device '{device.id}' already exists."
                )

            self._devices[device.id] = device

    def unregister(
        self,
        device_id: str,
    ) -> None:
        """
        Remove a device.
        """
        with self._lock:
            if device_id not in self._devices:
                raise DeviceNotFoundError(device_id)

            del self._devices[device_id]

    def get(
        self,
        device_id: str,
    ) -> BaseDevice:
        """
        Return a registered device.
        """
        try:
            return self._devices[device_id]
        except KeyError as exc:
            raise DeviceNotFoundError(device_id) from exc

    def exists(
        self,
        device_id: str,
    ) -> bool:
        """
        Check whether a device exists.
        """
        return device_id in self._devices

    def list(self) -> list[BaseDevice]:
        """
        Return all registered devices.
        """
        return list(self._devices.values())

    def list_by_category(
        self,
        category: DeviceCategory,
    ) -> list[BaseDevice]:
        """
        Return devices belonging to a category.
        """
        return [
            device
            for device in self._devices.values()
            if device.metadata.category == category
        ]

    def clear(self) -> None:
        """
        Remove all registered devices.
        """
        with self._lock:
            self._devices.clear()

    def __contains__(
        self,
        device_id: str,
    ) -> bool:
        return device_id in self._devices

    def __len__(self) -> int:
        return len(self._devices)

    def __iter__(self):
        return iter(self._devices.values())