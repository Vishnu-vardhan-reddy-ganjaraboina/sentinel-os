"""
Constants for the Sentinel Devices subsystem.
"""

from enum import StrEnum

DEFAULT_DEVICE_VERSION = "1.0.0"


class DeviceCategory(StrEnum):
    """
    Supported device categories.
    """

    FILESYSTEM = "filesystem"
    STORAGE = "storage"
    INPUT = "input"
    OUTPUT = "output"
    AUDIO = "audio"
    VIDEO = "video"
    DISPLAY = "display"
    NETWORK = "network"
    BLUETOOTH = "bluetooth"
    SERIAL = "serial"
    USB = "usb"
    SENSOR = "sensor"
    SYSTEM = "system"
    VIRTUAL = "virtual"
    CUSTOM = "custom"


class DeviceStatus(StrEnum):
    """
    Device status.
    """

    ONLINE = "online"
    OFFLINE = "offline"
    BUSY = "busy"
    DISCONNECTED = "disconnected"