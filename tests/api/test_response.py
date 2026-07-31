import pytest

from sentinel.api.constants import (
    ContentType,
    HTTPStatus,
)
from sentinel.api.response import APIResponse


def test_default_response():

    response = APIResponse()

    assert response.status_code == 200
    assert response.body is None
    assert (
        response.headers["Content-Type"]
        == ContentType.JSON.value
    )


def test_custom_response():

    response = APIResponse(
        status_code=HTTPStatus.CREATED,
        body={"id": 1},
    )

    assert response.status_code == 201
    assert response.body == {"id": 1}


def test_custom_headers():

    response = APIResponse(
        headers={
            "X-Test": "Sentinel",
        },
    )

    assert response.headers["X-Test"] == "Sentinel"


def test_to_dict():

    response = APIResponse()

    data = response.to_dict()

    assert data["status_code"] == 200
    assert "headers" in data
    assert "body" in data


def test_repr():

    response = APIResponse()

    assert "APIResponse" in repr(response)


def test_equality():

    a = APIResponse()
    b = APIResponse()

    assert a == b


def test_hash():

    response = APIResponse()

    assert isinstance(hash(response), int)


def test_invalid_status():

    with pytest.raises(TypeError):
        APIResponse(status_code=200)