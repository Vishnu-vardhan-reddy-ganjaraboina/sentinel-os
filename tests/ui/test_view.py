import pytest

from sentinel.ui.constants import ViewState
from sentinel.ui.view import UIView


def test_create_view():

    view = UIView("dashboard")

    assert view.name == "dashboard"
    assert view.state == ViewState.CREATED


def test_show():

    view = UIView("dashboard")

    view.show()

    assert view.state == ViewState.ACTIVE


def test_hide():

    view = UIView("dashboard")

    view.hide()

    assert view.state == ViewState.HIDDEN


def test_to_dict():

    view = UIView("dashboard")

    data = view.to_dict()

    assert data["name"] == "dashboard"
    assert data["state"] == ViewState.CREATED.value


def test_repr():

    view = UIView("dashboard")

    assert "UIView" in repr(view)


def test_equality():

    a = UIView("dashboard")
    b = UIView("dashboard")

    assert a == b


def test_hash():

    view = UIView("dashboard")

    assert isinstance(hash(view), int)


def test_invalid_name():

    with pytest.raises(ValueError):
        UIView("")