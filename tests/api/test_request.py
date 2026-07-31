import pytest

from sentinel.api.constants import HTTPMethod
from sentinel.api.request import APIRequest


def test_create_request():

    request = APIRequest(
        path="/users",
        method=HTTPMethod.GET,
    )

    assert request.path == "/users"
    assert request.method == HTTPMethod.GET
    assert request.headers == {}
    assert request.body is None


def test_custom_headers():

    request = APIRequest(
        "/",
        HTTPMethod.POST,
        headers={"Authorization": "Bearer token"},
    )

    assert request.headers["Authorization"] == "Bearer token"


def test_body():

    body = {"name": "Sentinel"}

    request = APIRequest(
        "/",
        HTTPMethod.POST,
        body=body,
    )

    assert request.body == body


def test_to_dict():

    request = APIRequest(
        "/health",
        HTTPMethod.GET,
    )

    data = request.to_dict()

    assert data["path"] == "/health"
    assert data["method"] == "GET"


def test_repr():

    request = APIRequest(
        "/",
        HTTPMethod.GET,
    )

    assert "APIRequest" in repr(request)


def test_equality():

    a = APIRequest("/", HTTPMethod.GET)
    b = APIRequest("/", HTTPMethod.GET)

    assert a == b


def test_hash():

    request = APIRequest("/", HTTPMethod.GET)

    assert isinstance(hash(request), int)


def test_invalid_path():

    with pytest.raises(ValueError):
        APIRequest("", HTTPMethod.GET)


def test_invalid_method():

    with pytest.raises(TypeError):
        APIRequest("/", "GET")