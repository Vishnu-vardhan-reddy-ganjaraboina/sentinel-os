"""
Authorization component for the Sentinel Kernel Control Plane.
"""

from __future__ import annotations

from collections.abc import Collection

from sentinel.control_plane.permissions import ControlPermission


class ControlAuthorizer:
    """
    Determine whether a caller has a required control permission.

    The authorizer intentionally knows nothing about commands or Kernel
    operations. Command-to-permission mapping belongs to ControlPolicy.
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

    def is_allowed(self, permission: ControlPermission) -> bool:
        """Return True when the required permission is granted."""
        return permission in self._permissions

    def require(self, permission: ControlPermission) -> None:
        """
        Require a permission.

        Raises
        ------
        PermissionError
            If the required permission has not been granted.
        """
        if not self.is_allowed(permission):
            raise PermissionError(
                f"Permission denied: '{permission.value}' permission required."
            )