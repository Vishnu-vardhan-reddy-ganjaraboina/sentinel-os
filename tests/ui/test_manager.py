import pytest

from sentinel.ui.exceptions import ViewNotFoundError
from sentinel.ui.manager import SentinelUIManager
from sentinel.ui.view import UIView
from sentinel.ui.window import UIWindow


def test_window_property():

    manager = SentinelUIManager()

    assert manager.window is None


def test_set_window():

    manager = SentinelUIManager()

    window = UIWindow("Sentinel")

    manager.set_window(window)

    assert manager.get_window() is window


def test_add_view():

    manager = SentinelUIManager()

    view = UIView("home")

    manager.add_view(view)

    assert len(manager) == 1


def test_get_view():

    manager = SentinelUIManager()

    view = UIView("home")

    manager.add_view(view)

    assert manager.get_view("home") is view


def test_remove_view():

    manager = SentinelUIManager()

    view = UIView("home")

    manager.add_view(view)

    manager.remove_view("home")

    assert len(manager) == 0


def test_missing_view():

    manager = SentinelUIManager()

    with pytest.raises(ViewNotFoundError):
        manager.get_view("missing")


def test_views():

    manager = SentinelUIManager()

    manager.add_view(UIView("one"))
    manager.add_view(UIView("two"))

    assert len(manager.views()) == 2


def test_clear():

    manager = SentinelUIManager()

    manager.add_view(UIView("home"))
    manager.set_window(UIWindow("Sentinel"))

    manager.clear()

    assert len(manager) == 0
    assert manager.window is None


def test_to_dict():

    manager = SentinelUIManager()

    manager.set_window(UIWindow("Sentinel"))
    manager.add_view(UIView("home"))

    data = manager.to_dict()

    assert data["window"]["title"] == "Sentinel"
    assert len(data["views"]) == 1