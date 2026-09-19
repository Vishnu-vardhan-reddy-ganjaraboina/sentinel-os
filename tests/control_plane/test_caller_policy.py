from sentinel.control_plane.caller_policy import ControlCallerPolicy
from sentinel.control_plane.callers import ControlCallerType
from sentinel.control_plane.permissions import ControlPermission


def test_system_has_read_and_control_permissions() -> None:
    permissions = ControlCallerPolicy.permissions_for(
        ControlCallerType.SYSTEM
    )

    assert permissions == frozenset(
        {
            ControlPermission.READ,
            ControlPermission.CONTROL,
        }
    )


def test_cli_has_read_and_control_permissions() -> None:
    permissions = ControlCallerPolicy.permissions_for(
        ControlCallerType.CLI
    )

    assert permissions == frozenset(
        {
            ControlPermission.READ,
            ControlPermission.CONTROL,
        }
    )


def test_api_is_read_only_by_default() -> None:
    permissions = ControlCallerPolicy.permissions_for(
        ControlCallerType.API
    )

    assert permissions == frozenset(
        {
            ControlPermission.READ,
        }
    )


def test_automation_has_read_and_control_permissions() -> None:
    permissions = ControlCallerPolicy.permissions_for(
        ControlCallerType.AUTOMATION
    )

    assert permissions == frozenset(
        {
            ControlPermission.READ,
            ControlPermission.CONTROL,
        }
    )


def test_ai_agent_is_read_only_by_default() -> None:
    permissions = ControlCallerPolicy.permissions_for(
        ControlCallerType.AI_AGENT
    )

    assert permissions == frozenset(
        {
            ControlPermission.READ,
        }
    )