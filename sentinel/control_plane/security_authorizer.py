from __future__ import annotations

from sentinel.security.constants import Permission
from sentinel.security.service import SecurityService

from .context import ControlContext
from .permissions import ControlPermission


class SecurityControlAuthorizer:
    """
    Control Plane authorization adapter backed by Sentinel SecurityService.

    This adapter translates Control Plane permissions into the existing
    Sentinel Security permission model.

    Mapping:
        ControlPermission.READ
            -> Permission.READ

        ControlPermission.CONTROL
            -> Permission.EXECUTE
    """

    __slots__ = ("_security",)

    _PERMISSION_MAP = {
        ControlPermission.READ: Permission.READ,
        ControlPermission.CONTROL: Permission.EXECUTE,
    }

    def __init__(self, security: SecurityService) -> None:
        if not isinstance(security, SecurityService):
            raise TypeError(
                "security must be a SecurityService."
            )

        self._security = security

    @property
    def security(self) -> SecurityService:
        """Return the backing SecurityService."""
        return self._security

    @classmethod
    def map_permission(
        cls,
        permission: ControlPermission,
    ) -> Permission:
        """
        Translate a Control Plane permission into a Security permission.
        """
        try:
            return cls._PERMISSION_MAP[permission]
        except KeyError as exc:
            raise ValueError(
                f"Unsupported control permission: '{permission}'."
            ) from exc

    def is_allowed(
        self,
        context: ControlContext,
        permission: ControlPermission,
    ) -> bool:
        """
        Resolve the caller identity and ask SecurityService whether
        the caller has the required permission.
        """
        security_permission = self.map_permission(permission)

        identity = self._security.get_identity(
            context.caller_id
        )

        if identity is None:
            return False

        return self._security.authorize(
            identity,
            security_permission,
        )

    def require(
        self,
        context: ControlContext,
        permission: ControlPermission,
    ) -> None:
        """
        Require the caller to have the requested permission.
        """
        if not self.is_allowed(context, permission):
            raise PermissionError(
                f"Permission denied: "
                f"'{permission.value}' permission required."
            )