"""
Exceptions for the Sentinel Devices subsystem.
"""

from sentinel.core.exceptions import SentinelError


class DeviceError(SentinelError):
    """
    Base exception for all device-related errors.
    """


class DeviceNotFoundError(DeviceError):
    """
    Raised when a device cannot be found.
    """


class DeviceAlreadyExistsError(DeviceError):
    """
    Raised when attempting to register an existing device.
    """


class DeviceDisconnectedError(DeviceError):
    """
    Raised when attempting to use a disconnected device.
    """


class DeviceBusyError(DeviceError):
    """
    Raised when a device is busy.
    """


class InvalidDeviceError(DeviceError):
    """
    Raised when an invalid device is encountered.
    """


class DeviceOperationError(DeviceError):
    """
    Raised when a device operation fails.
    """