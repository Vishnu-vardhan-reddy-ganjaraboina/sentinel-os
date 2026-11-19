"""
Device registry for the Sentinel Devices subsystem.
"""

from __future__ import annotations

import builtins
from collections.abc import Iterator
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
        """Register a device."""
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
        """Remove a device."""
        with self._lock:
            if device_id not in self._devices:
                raise DeviceNotFoundError(device_id)

            del self._devices[device_id]

    def get(
        self,
        device_id: str,
    ) -> BaseDevice:
        """Return a registered device."""
        with self._lock:
            try:
                return self._devices[device_id]
            except KeyError as exc:
                raise DeviceNotFoundError(device_id) from exc

    def exists(
        self,
        device_id: str,
    ) -> bool:
        """Check whether a device exists."""
        with self._lock:
            return device_id in self._devices

    def list(self) -> builtins.list[BaseDevice]:
        """Return all registered devices."""
        with self._lock:
            return list(self._devices.values())

    def list_by_category(
        self,
        category: DeviceCategory,
    ) -> builtins.list[BaseDevice]:
        """Return devices belonging to a category."""
        with self._lock:
            return [
                device
                for device in self._devices.values()
                if device.metadata.category == category
            ]

    def clear(self) -> None:
        """Remove all registered devices."""
        with self._lock:
            self._devices.clear()

    def __contains__(
        self,
        device_id: str,
    ) -> bool:
        with self._lock:
            return device_id in self._devices

    def __len__(self) -> int:
        with self._lock:
            return len(self._devices)

    def __iter__(self) -> Iterator[BaseDevice]:
        with self._lock:
            snapshot = list(self._devices.values())

        return iter(snapshot)
