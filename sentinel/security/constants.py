"""
Constants for the Sentinel Security subsystem.
"""

from __future__ import annotations

from enum import Enum

DEFAULT_SECURITY_VERSION = "1.0.0"


class Role(Enum):
    """
    Built-in security roles.
    """

    ADMIN = "admin"
    SYSTEM = "system"
    USER = "user"
    GUEST = "guest"


class Permission(Enum):
    """
    Built-in permissions.
    """

    READ = "read"
    WRITE = "write"
    EXECUTE = "execute"
    DELETE = "delete"
    CONFIGURE = "configure"


class AuthenticationStatus(Enum):
    """
    Authentication states.
    """

    AUTHENTICATED = "authenticated"
    UNAUTHENTICATED = "unauthenticated"
    FAILED = "failed"


class AuthorizationStatus(Enum):
    """
    Authorization states.
    """

    ALLOWED = "allowed"
    DENIED = "denied"