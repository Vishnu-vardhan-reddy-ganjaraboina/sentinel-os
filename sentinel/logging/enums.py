"""
Enumerations for the Sentinel logging runtime.
"""

from __future__ import annotations

from enum import IntEnum


class LogLevel(IntEnum):
    """
    Severity levels supported by the Sentinel logging runtime.
    """

    DEBUG = 10
    INFO = 20
    WARNING = 30
    ERROR = 40
    CRITICAL = 50


__all__ = (
    "LogLevel",
)