import pytest

from sentinel.api.constants import HTTPMethod
from sentinel.api.exceptions import (
    MethodNotAllowedError,
    RouteNotFoundError,
)
from sentinel.api.router import APIRouter


def sample_handler():
    return {"success": True}


def test_add_route():

    router = APIRouter()

    router.add_route(
        HTTPMethod.GET,
        "/",
        sample_handler,
    )

    assert len(router) == 1


def test_resolve_route():

    router = APIRouter()

    router.add_route(
        HTTPMethod.GET,
        "/",
        sample_handler,
    )

    handler = router.resolve(
        HTTPMethod.GET,
        "/",
    )

    assert handler is sample_handler


def test_duplicate_route():

    router = APIRouter()

    router.add_route(
        HTTPMethod.GET,
        "/",
        sample_handler,
    )

    with pytest.raises(ValueError):
        router.add_route(
            HTTPMethod.GET,
            "/",
            sample_handler,
        )


def test_route_not_found():

    router = APIRouter()

    with pytest.raises(RouteNotFoundError):
        router.resolve(
            HTTPMethod.GET,
            "/missing",
        )


def test_invalid_method_add():

    router = APIRouter()

    with pytest.raises(MethodNotAllowedError):
        router.add_route(
            "GET",
            "/",
            sample_handler,
        )


def test_invalid_method_resolve():

    router = APIRouter()

    with pytest.raises(MethodNotAllowedError):
        router.resolve(
            "GET",
            "/",
        )


def test_contains():

    router = APIRouter()

    router.add_route(
        HTTPMethod.GET,
        "/",
        sample_handler,
    )

    assert (HTTPMethod.GET, "/") in router


def test_clear():

    router = APIRouter()

    router.add_route(
        HTTPMethod.GET,
        "/",
        sample_handler,
    )

    router.clear()

    assert len(router) == 0