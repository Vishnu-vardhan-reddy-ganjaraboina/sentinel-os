"""
Exceptions for the Sentinel Security subsystem.
"""

from __future__ import annotations


class SecurityError(Exception):
    """
    Base exception for all security-related errors.
    """


class AuthenticationError(SecurityError):
    """
    Raised when authentication fails.
    """


class AuthorizationError(SecurityError):
    """
    Raised when authorization fails.
    """


class IdentityError(SecurityError):
    """
    Raised for invalid identity operations.
    """


class CredentialError(SecurityError):
    """
    Raised for credential-related errors.
    """


class PermissionError(SecurityError):
    """
    Raised when permission validation fails.
    """