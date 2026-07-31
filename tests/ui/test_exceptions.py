import pytest

from sentinel.ui.exceptions import (
    ThemeError,
    UIError,
    ViewError,
    ViewNotFoundError,
    WindowError,
    WindowNotFoundError,
)


def test_ui_error():
    with pytest.raises(UIError):
        raise UIError("ui")


def test_view_error():
    with pytest.raises(ViewError):
        raise ViewError("view")


def test_window_error():
    with pytest.raises(WindowError):
        raise WindowError("window")


def test_theme_error():
    with pytest.raises(ThemeError):
        raise ThemeError("theme")


def test_view_not_found():
    with pytest.raises(ViewNotFoundError):
        raise ViewNotFoundError("missing")


def test_window_not_found():
    with pytest.raises(WindowNotFoundError):
        raise WindowNotFoundError("missing")


def test_inheritance():
    assert issubclass(ViewError, UIError)
    assert issubclass(WindowError, UIError)
    assert issubclass(ThemeError, UIError)
    assert issubclass(ViewNotFoundError, UIError)
    assert issubclass(WindowNotFoundError, UIError)