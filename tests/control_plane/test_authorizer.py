from __future__ import annotations

import pytest

from sentinel.control_plane.authorizer import ControlAuthorizer
from sentinel.control_plane.permissions import ControlPermission


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

    assert authorizer.is_allowed(ControlPermission.READ) is True


def test_authorizer_denies_missing_permission() -> None:
    authorizer = ControlAuthorizer(
        {
            ControlPermission.READ,
        }
    )

    assert authorizer.is_allowed(ControlPermission.CONTROL) is False


def test_require_allows_granted_permission() -> None:
    authorizer = ControlAuthorizer(
        {
            ControlPermission.CONTROL,
        }
    )

    authorizer.require(ControlPermission.CONTROL)


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
        authorizer.require(ControlPermission.CONTROL)


def test_authorizer_permissions_are_immutable() -> None:
    permissions = {ControlPermission.READ}
    authorizer = ControlAuthorizer(permissions)

    permissions.add(ControlPermission.CONTROL)

    assert authorizer.permissions == {
        ControlPermission.READ,
    }