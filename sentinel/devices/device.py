"""
Base implementation of a Sentinel device.
"""

from __future__ import annotations

from abc import abstractmethod
from typing import Any

from sentinel.devices.exceptions import (
    DeviceDisconnectedError,
)
from sentinel.devices.interfaces import Device
from sentinel.devices.metadata import DeviceMetadata


class BaseDevice(Device):
    """
    Base implementation for Sentinel devices.

    Concrete devices should inherit from this class and implement
    the `run()` method.
    """

    def __init__(
        self,
        metadata: DeviceMetadata,
    ) -> None:
        self._metadata = metadata

    @property
    def metadata(self) -> DeviceMetadata:
        """
        Return the device metadata.
        """
        return self._metadata

    @property
    def id(self) -> str:
        return self._metadata.device_id

    @property
    def name(self) -> str:
        return self._metadata.name

    @property
    def description(self) -> str:
        return self._metadata.description

    @property
    def version(self) -> str:
        return self._metadata.version

    @property
    def connected(self) -> bool:
        return self._metadata.connected

    def connect(self) -> None:
        """
        Connect the device.
        """
        self._metadata.connected = True

    def disconnect(self) -> None:
        """
        Disconnect the device.
        """
        self._metadata.connected = False

    def health_check(self) -> bool:
        """
        Default health check implementation.
        """
        return self.connected

    def execute(
        self,
        **kwargs: Any,
    ) -> Any:
        """
        Execute a device operation.
        """
        if not self.connected:
            raise DeviceDisconnectedError(
                f"Device '{self.id}' is disconnected."
            )

        return self.run(**kwargs)

    @abstractmethod
    def run(
        self,
        **kwargs: Any,
    ) -> Any:
        """
        Execute the concrete device implementation.
        """