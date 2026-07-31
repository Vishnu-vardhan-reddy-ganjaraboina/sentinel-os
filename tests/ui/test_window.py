import pytest

from sentinel.ui.constants import (
    Theme,
    WindowState,
)
from sentinel.ui.window import UIWindow


def test_create_window():

    window = UIWindow("Sentinel")

    assert window.title == "Sentinel"
    assert window.theme == Theme.SYSTEM
    assert window.state == WindowState.CREATED


def test_open():

    window = UIWindow("Sentinel")

    window.open()

    assert window.state == WindowState.OPEN


def test_minimize():

    window = UIWindow("Sentinel")

    window.minimize()

    assert window.state == WindowState.MINIMIZED


def test_close():

    window = UIWindow("Sentinel")

    window.close()

    assert window.state == WindowState.CLOSED


def test_to_dict():

    window = UIWindow("Sentinel")

    data = window.to_dict()

    assert data["title"] == "Sentinel"
    assert data["theme"] == Theme.SYSTEM.value
    assert data["state"] == WindowState.CREATED.value


def test_repr():

    window = UIWindow("Sentinel")

    assert "UIWindow" in repr(window)


def test_equality():

    a = UIWindow("Sentinel")
    b = UIWindow("Sentinel")

    assert a == b


def test_hash():

    window = UIWindow("Sentinel")

    assert isinstance(hash(window), int)


def test_invalid_title():

    with pytest.raises(ValueError):
        UIWindow("")


def test_invalid_theme():

    with pytest.raises(TypeError):
        UIWindow(
            "Sentinel",
            theme="dark",
        )