"""
Exceptions for the Sentinel UI subsystem.
"""

from __future__ import annotations


class UIError(Exception):
    """
    Base exception for all UI-related errors.
    """


class ViewError(UIError):
    """
    Raised when a view operation fails.
    """


class WindowError(UIError):
    """
    Raised when a window operation fails.
    """


class ThemeError(UIError):
    """
    Raised when an invalid theme is used.
    """


class ViewNotFoundError(UIError):
    """
    Raised when a requested view cannot be found.
    """


class WindowNotFoundError(UIError):
    """
    Raised when a requested window cannot be found.
    """