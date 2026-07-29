"""
Interfaces for the Sentinel Devices subsystem.
"""

from __future__ import annotations

from abc import ABC, abstractmethod


class Device(ABC):
    """
    Abstract interface for Sentinel devices.
    """

    @property
    @abstractmethod
    def id(self) -> str:
        """
        Unique device identifier.
        """

    @property
    @abstractmethod
    def name(self) -> str:
        """
        Human-readable device name.
        """

    @property
    @abstractmethod
    def description(self) -> str:
        """
        Device description.
        """

    @property
    @abstractmethod
    def version(self) -> str:
        """
        Device version.
        """

    @property
    @abstractmethod
    def connected(self) -> bool:
        """
        Whether the device is connected.
        """

    @abstractmethod
    def connect(self) -> None:
        """
        Connect the device.
        """

    @abstractmethod
    def disconnect(self) -> None:
        """
        Disconnect the device.
        """

    @abstractmethod
    def health_check(self) -> bool:
        """
        Check whether the device is healthy.
        """

    @abstractmethod
    def execute(self, **kwargs):
        """
        Execute a device-specific operation.
        """