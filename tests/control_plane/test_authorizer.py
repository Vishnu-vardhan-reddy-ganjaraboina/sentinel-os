from __future__ import annotations

import pytest

from sentinel.control_plane.authorizer import ControlAuthorizer
from sentinel.control_plane.context import ControlContext
from sentinel.control_plane.permissions import ControlPermission
from sentinel.control_plane.callers import ControlCallerType


def create_context() -> ControlContext:
    return ControlContext(
        caller_id="local-cli",
        caller_type="cli",
    )


def test_authorizer_stores_permissions() -> None:
    authorizer = ControlAuthorizer(
        {
            ControlPermission.READ,
            ControlPermission.CONTROL,
        }
    )

    assert authorizer.permissions == {
        ControlPermission.READ,
        ControlPermission.CONTROL,
    }


def test_authorizer_allows_granted_permission() -> None:
    authorizer = ControlAuthorizer(
        {
            ControlPermission.READ,
        }
    )

    assert authorizer.is_allowed(
        create_context(),
        ControlPermission.READ,
    ) is True


def test_authorizer_denies_missing_permission() -> None:
    authorizer = ControlAuthorizer(
        {
            ControlPermission.READ,
        }
    )

    assert authorizer.is_allowed(
        create_context(),
        ControlPermission.CONTROL,
    ) is False


def test_require_allows_granted_permission() -> None:
    authorizer = ControlAuthorizer(
        {
            ControlPermission.CONTROL,
        }
    )

    authorizer.require(
        create_context(),
        ControlPermission.CONTROL,
    )


def test_require_raises_for_missing_permission() -> None:
    authorizer = ControlAuthorizer(
        {
            ControlPermission.READ,
        }
    )

    with pytest.raises(
        PermissionError,
        match="Permission denied: 'control' permission required.",
    ):
        authorizer.require(
            create_context(),
            ControlPermission.CONTROL,
        )


def test_authorizer_permissions_are_immutable() -> None:
    permissions = {ControlPermission.READ}
    authorizer = ControlAuthorizer(permissions)

    permissions.add(ControlPermission.CONTROL)

    assert authorizer.permissions == {
        ControlPermission.READ,
    }


def test_identity_does_not_automatically_grant_permission() -> None:
    authorizer = ControlAuthorizer(
        {
            ControlPermission.READ,
        }
    )

    privileged_identity = ControlContext(
        caller_id="sentinel-agent",
        caller_type="system_agent",
    )

    assert authorizer.is_allowed(
        privileged_identity,
        ControlPermission.CONTROL,
    ) is False

def test_from_context_uses_caller_policy() -> None:
    context = ControlContext(
        caller_id="test-ai",
        caller_type=ControlCallerType.AI_AGENT,
    )

    authorizer = ControlAuthorizer.from_context(context)

    assert authorizer.permissions == frozenset(
        {
            ControlPermission.READ,
        }
    )


def test_from_context_allows_system_control() -> None:
    context = ControlContext(
        caller_id="system",
        caller_type=ControlCallerType.SYSTEM,
    )

    authorizer = ControlAuthorizer.from_context(context)

    assert authorizer.permissions == frozenset(
        {
            ControlPermission.READ,
            ControlPermission.CONTROL,
        }
    )