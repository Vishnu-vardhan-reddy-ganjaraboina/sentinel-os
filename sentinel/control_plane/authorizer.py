"""
Authorization component for the Sentinel Kernel Control Plane.
"""

from __future__ import annotations

from collections.abc import Collection

from sentinel.control_plane.context import ControlContext
from sentinel.control_plane.permissions import ControlPermission


class ControlAuthorizer:
    """
    Determine whether a caller has a required control permission.

    Caller identity and permissions remain separate concerns. The context
    provides caller information, while the configured permissions determine
    what the caller may do.
    """

    __slots__ = ("_permissions",)

    def __init__(
        self,
        permissions: Collection[ControlPermission],
    ) -> None:
        self._permissions = frozenset(permissions)

    @property
    def permissions(self) -> frozenset[ControlPermission]:
        """Return the permissions granted to this authorizer."""
        return self._permissions

    def is_allowed(
        self,
        context: ControlContext,
        permission: ControlPermission,
    ) -> bool:
        """
        Return True when the caller has the required permission.

        The current implementation does not make authorization decisions
        based on caller identity. The context is available so richer
        authorization policies can be introduced without changing the
        Control Plane contract later.
        """
        _ = context
        return permission in self._permissions

    def require(
        self,
        context: ControlContext,
        permission: ControlPermission,
    ) -> None:
        """
        Require a permission for a caller.

        Raises
        ------
        PermissionError
            If the required permission has not been granted.
        """
        if not self.is_allowed(context, permission):
            raise PermissionError(
                f"Permission denied: '{permission.value}' permission required."
            )