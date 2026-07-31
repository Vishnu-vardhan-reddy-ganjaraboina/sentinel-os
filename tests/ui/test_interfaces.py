import pytest

from sentinel.ui.constants import (
    Theme,
    ViewState,
    WindowState,
)
from sentinel.ui.interfaces import (
    UIManager,
    View,
    Window,
)


class DummyView(View):

    def __init__(self):
        self._state = ViewState.CREATED

    @property
    def name(self):
        return "home"

    @property
    def state(self):
        return self._state

    def show(self):
        self._state = ViewState.ACTIVE

    def hide(self):
        self._state = ViewState.HIDDEN

    def to_dict(self):
        return {
            "name": self.name,
            "state": self.state.value,
        }


class DummyWindow(Window):

    def __init__(self):
        self._state = WindowState.CREATED
        self._theme = Theme.SYSTEM

    @property
    def title(self):
        return "Sentinel"

    @property
    def state(self):
        return self._state

    @property
    def theme(self):
        return self._theme

    def open(self):
        self._state = WindowState.OPEN

    def minimize(self):
        self._state = WindowState.MINIMIZED

    def close(self):
        self._state = WindowState.CLOSED

    def to_dict(self):
        return {
            "title": self.title,
            "state": self.state.value,
            "theme": self.theme.value,
        }


class DummyUIManager(UIManager):

    def __init__(self):
        self._views = {}
        self._window = None

    def add_view(self, view):
        self._views[view.name] = view

    def remove_view(self, name):
        self._views.pop(name)

    def get_view(self, name):
        return self._views[name]

    def set_window(self, window):
        self._window = window

    def get_window(self):
        return self._window

    def views(self):
        return list(self._views.values())

    def clear(self):
        self._views.clear()
        self._window = None

    def to_dict(self):
        return {
            "window": self._window.to_dict() if self._window else None,
            "views": [
                view.to_dict()
                for view in self._views.values()
            ],
        }


def test_view():

    view = DummyView()

    assert view.name == "home"

    view.show()
    assert view.state == ViewState.ACTIVE

    view.hide()
    assert view.state == ViewState.HIDDEN

    assert view.to_dict()["name"] == "home"


def test_window():

    window = DummyWindow()

    assert window.title == "Sentinel"

    window.open()
    assert window.state == WindowState.OPEN

    window.minimize()
    assert window.state == WindowState.MINIMIZED

    window.close()
    assert window.state == WindowState.CLOSED

    assert window.to_dict()["theme"] == Theme.SYSTEM.value


def test_manager():

    manager = DummyUIManager()

    view = DummyView()
    window = DummyWindow()

    manager.add_view(view)
    manager.set_window(window)

    assert manager.get_view("home") is view
    assert manager.get_window() is window

    assert len(manager.views()) == 1

    data = manager.to_dict()

    assert data["window"]["title"] == "Sentinel"
    assert len(data["views"]) == 1
    assert data["views"][0]["name"] == "home"

    manager.remove_view("home")

    assert manager.views() == []

    manager.clear()

    assert manager.get_window() is None
    assert manager.views() == []


def test_view_is_abstract():
    with pytest.raises(TypeError):
        View()


def test_window_is_abstract():
    with pytest.raises(TypeError):
        Window()


def test_manager_is_abstract():
    with pytest.raises(TypeError):
        UIManager()