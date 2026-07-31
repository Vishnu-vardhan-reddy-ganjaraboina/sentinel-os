import pytest

from sentinel.api.exceptions import (
    APIError,
    MethodNotAllowedError,
    RequestError,
    ResponseError,
    RouteNotFoundError,
    ServerError,
)


def test_api_error():
    with pytest.raises(APIError):
        raise APIError("api")


def test_request_error():
    with pytest.raises(RequestError):
        raise RequestError("request")


def test_response_error():
    with pytest.raises(ResponseError):
        raise ResponseError("response")


def test_route_not_found_error():
    with pytest.raises(RouteNotFoundError):
        raise RouteNotFoundError("route")


def test_method_not_allowed_error():
    with pytest.raises(MethodNotAllowedError):
        raise MethodNotAllowedError("method")


def test_server_error():
    with pytest.raises(ServerError):
        raise ServerError("server")


def test_inheritance():
    assert issubclass(RequestError, APIError)
    assert issubclass(ResponseError, APIError)
    assert issubclass(RouteNotFoundError, APIError)
    assert issubclass(MethodNotAllowedError, APIError)
    assert issubclass(ServerError, APIError)