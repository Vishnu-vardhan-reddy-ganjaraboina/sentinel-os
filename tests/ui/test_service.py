from sentinel.ui.service import UIService
from sentinel.ui.view import UIView
from sentinel.ui.window import UIWindow


def test_manager_property():

    service = UIService()

    assert service.manager is not None


def test_add_get_view():

    service = UIService()

    view = UIView("home")

    service.add_view(view)

    assert service.get_view("home") is view


def test_set_get_window():

    service = UIService()

    window = UIWindow("Sentinel")

    service.set_window(window)

    assert service.get_window() is window


def test_views():

    service = UIService()

    service.add_view(UIView("home"))
    service.add_view(UIView("settings"))

    assert len(service.views()) == 2


def test_remove_view():

    service = UIService()

    service.add_view(UIView("home"))

    service.remove_view("home")

    assert service.views() == []


def test_clear():

    service = UIService()

    service.add_view(UIView("home"))
    service.set_window(UIWindow("Sentinel"))

    service.clear()

    assert service.views() == []
    assert service.get_window() is None


def test_to_dict():

    service = UIService()

    service.add_view(UIView("home"))
    service.set_window(UIWindow("Sentinel"))

    data = service.to_dict()

    assert data["window"]["title"] == "Sentinel"
    assert len(data["views"]) == 1


def test_len():

    service = UIService()

    service.add_view(UIView("one"))
    service.add_view(UIView("two"))

    assert len(service) == 2