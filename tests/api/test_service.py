from sentinel.api.constants import (
    HTTPMethod,
    ResponseStatus,
)
from sentinel.api.manager import APIManager
from sentinel.api.request import APIRequest
from sentinel.api.service import APIService


def hello(request):
    return {
        "message": "Hello from API Service"
    }


def test_manager_property():

    manager = APIManager()
    service = APIService(manager)

    assert service.manager is manager


def test_add_route():

    service = APIService()

    service.add_route(
        HTTPMethod.GET,
        "/hello",
        hello,
    )

    assert len(service) == 1


def test_handle():

    service = APIService()

    service.add_route(
        HTTPMethod.GET,
        "/hello",
        hello,
    )

    response = service.handle(
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
        == "Hello from API Service"
    )


def test_clear():

    service = APIService()

    service.add_route(
        HTTPMethod.GET,
        "/hello",
        hello,
    )

    assert len(service) == 1

    service.clear()

    assert len(service) == 0