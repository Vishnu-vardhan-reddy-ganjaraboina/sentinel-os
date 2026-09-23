from __future__ import annotations

from typing import Protocol

from .context import ControlContext
from .permissions import ControlPermission


class ControlAuthorizerProtocol(Protocol):
    """
    Authorization contract used by the Kernel Control Plane.

    Implementations may use the built-in Control Plane permission model,
    the Sentinel Security subsystem, or another compatible authorization
    backend.
    """

    def is_allowed(
        self,
        context: ControlContext,
        permission: ControlPermission,
    ) -> bool:
        """Return whether the context has the requested permission."""
        ...

    def require(
        self,
        context: ControlContext,
        permission: ControlPermission,
    ) -> None:
        """Raise PermissionError when the permission is not granted."""
        ...