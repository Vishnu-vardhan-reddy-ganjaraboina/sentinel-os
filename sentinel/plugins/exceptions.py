"""
Exceptions for the Sentinel Plugin subsystem.
"""

from __future__ import annotations


class PluginError(Exception):
    """
    Base exception for all plugin-related errors.
    """


class PluginRegistrationError(PluginError):
    """
    Raised when plugin registration fails.
    """


class PluginLoadError(PluginError):
    """
    Raised when loading a plugin fails.
    """


class PluginUnloadError(PluginError):
    """
    Raised when unloading a plugin fails.
    """


class PluginEnableError(PluginError):
    """
    Raised when enabling a plugin fails.
    """


class PluginDisableError(PluginError):
    """
    Raised when disabling a plugin fails.
    """


class PluginNotFoundError(PluginError):
    """
    Raised when a plugin cannot be found.
    """


class PluginCleanupError(PluginError):
    """
    Raised when one or more plugins cannot be safely cleaned up.

    The original cleanup failures are preserved in the exception's
    ``__cause__`` or exception-group structure where applicable.
    """