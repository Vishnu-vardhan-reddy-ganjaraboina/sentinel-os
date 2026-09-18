from __future__ import annotations

from sentinel.control_plane.permissions import ControlPermission


def test_control_permissions_are_string_enums() -> None:
    assert ControlPermission.READ.value == "read"
    assert ControlPermission.CONTROL.value == "control"


def test_control_permission_order_is_stable() -> None:
    assert list(ControlPermission) == [
        ControlPermission.READ,
        ControlPermission.CONTROL,
    ]