from sentinel.ui.constants import (
    DEFAULT_UI_VERSION,
    Theme,
    ViewState,
    WindowState,
)


def test_version():
    assert DEFAULT_UI_VERSION == "1.0.0"


def test_theme():
    assert Theme.LIGHT.value == "light"
    assert Theme.DARK.value == "dark"
    assert Theme.SYSTEM.value == "system"


def test_window_state():
    assert WindowState.CREATED.value == "created"
    assert WindowState.OPEN.value == "open"
    assert WindowState.MINIMIZED.value == "minimized"
    assert WindowState.CLOSED.value == "closed"


def test_view_state():
    assert ViewState.CREATED.value == "created"
    assert ViewState.ACTIVE.value == "active"
    assert ViewState.HIDDEN.value == "hidden"