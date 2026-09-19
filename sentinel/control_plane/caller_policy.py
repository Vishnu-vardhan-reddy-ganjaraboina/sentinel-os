from __future__ import annotations

from sentinel.control_plane.callers import ControlCallerType
from sentinel.control_plane.permissions import ControlPermission


class ControlCallerPolicy:
    """
    Defines the default permissions associated with Control Plane callers.
    """

    _CALLER_PERMISSIONS = {
        ControlCallerType.SYSTEM: frozenset(
            {
                ControlPermission.READ,
                ControlPermission.CONTROL,
            }
        ),
        ControlCallerType.CLI: frozenset(
            {
                ControlPermission.READ,
                ControlPermission.CONTROL,
            }
        ),
        ControlCallerType.API: frozenset(
            {
                ControlPermission.READ,
            }
        ),
        ControlCallerType.AUTOMATION: frozenset(
            {
                ControlPermission.READ,
                ControlPermission.CONTROL,
            }
        ),
        ControlCallerType.AI_AGENT: frozenset(
            {
                ControlPermission.READ,
            }
        ),
    }

    @classmethod
    def permissions_for(
        cls,
        caller_type: ControlCallerType | str,
    ) -> frozenset[ControlPermission]:
        if isinstance(caller_type, ControlCallerType):
            caller = caller_type
        else:
            try:
                caller = ControlCallerType(caller_type)
            except ValueError:
                return frozenset()

        return cls._CALLER_PERMISSIONS.get(
            caller,
            frozenset(),
        )