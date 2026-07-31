from sentinel.api.constants import (
    HTTPMethod,
    ResponseStatus,
)
from sentinel.api.manager import APIManager
from sentinel.api.request import APIRequest


def hello(request):
    return {"message": "Hello API"}


def test_router_property():

    manager = APIManager()

    assert manager.router is not None


def test_server_property():

    manager = APIManager()

    assert manager.server is not None


def test_add_route():

    manager = APIManager()

    manager.add_route(
        HTTPMethod.GET,
        "/hello",
        hello,
    )

    assert len(manager) == 1


def test_handle():

    manager = APIManager()

    manager.add_route(
        HTTPMethod.GET,
        "/hello",
        hello,
    )

    response = manager.handle(
        APIRequest(
            "/hello",
            HTTPMethod.GET,
        )
    )

    assert response.status_code == 200
    assert (
        response.body["status"]
        == ResponseStatus.SUCCESS.value
    )
    assert (
        response.body["data"]["message"]
        == "Hello API"
    )


def test_clear():

    manager = APIManager()

    manager.add_route(
        HTTPMethod.GET,
        "/hello",
        hello,
    )

    assert len(manager) == 1

    manager.clear()

    assert len(manager) == 0