from sentinel.api.constants import (
    HTTPMethod,
    HTTPStatus,
    ResponseStatus,
)
from sentinel.api.request import APIRequest
from sentinel.api.response import APIResponse
from sentinel.api.router import APIRouter
from sentinel.api.server import APIServer


def hello(request):
    return {
        "message": "Hello Sentinel"
    }


def response_handler(request):
    return APIResponse(
        status_code=HTTPStatus.CREATED,
        body={
            "created": True,
        },
    )


def failing_handler(request):
    raise RuntimeError("boom")


def test_server_property():

    router = APIRouter()
    server = APIServer(router)

    assert server.router is router


def test_handle_success():

    router = APIRouter()

    router.add_route(
        HTTPMethod.GET,
        "/hello",
        hello,
    )

    server = APIServer(router)

    response = server.handle(
        APIRequest(
            "/hello",
            HTTPMethod.GET,
        )
    )

    assert response.status_code == 200
    assert response.body["status"] == ResponseStatus.SUCCESS.value
    assert response.body["data"]["message"] == "Hello Sentinel"


def test_handle_api_response():

    router = APIRouter()

    router.add_route(
        HTTPMethod.POST,
        "/create",
        response_handler,
    )

    server = APIServer(router)

    response = server.handle(
        APIRequest(
            "/create",
            HTTPMethod.POST,
        )
    )

    assert response.status_code == 201
    assert response.body["created"] is True


def test_route_not_found():

    server = APIServer()

    response = server.handle(
        APIRequest(
            "/missing",
            HTTPMethod.GET,
        )
    )

    assert response.status_code == 404
    assert response.body["status"] == ResponseStatus.ERROR.value


def test_handler_exception():

    router = APIRouter()

    router.add_route(
        HTTPMethod.GET,
        "/fail",
        failing_handler,
    )

    server = APIServer(router)

    response = server.handle(
        APIRequest(
            "/fail",
            HTTPMethod.GET,
        )
    )

    assert response.status_code == 500
    assert response.body["status"] == ResponseStatus.ERROR.value