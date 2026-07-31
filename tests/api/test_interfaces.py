import pytest

from sentinel.api.constants import HTTPMethod
from sentinel.api.interfaces import (
    Request,
    Response,
    Router,
    Server,
)


class DummyRequest(Request):

    @property
    def path(self):
        return "/"

    @property
    def method(self):
        return HTTPMethod.GET

    @property
    def headers(self):
        return {}

    @property
    def body(self):
        return None

    def to_dict(self):
        return {
            "path": self.path,
            "method": self.method.value,
            "headers": self.headers,
            "body": self.body,
        }


class DummyResponse(Response):

    @property
    def status_code(self):
        return 200

    @property
    def headers(self):
        return {}

    @property
    def body(self):
        return {"ok": True}

    def to_dict(self):
        return {
            "status_code": self.status_code,
            "headers": self.headers,
            "body": self.body,
        }


class DummyRouter(Router):

    def __init__(self):
        self.routes = {}

    def add_route(self, method, path, handler):
        self.routes[(method, path)] = handler

    def resolve(self, method, path):
        return self.routes[(method, path)]


class DummyServer(Server):

    def handle(self, request):
        return DummyResponse()


def test_request():
    req = DummyRequest()

    assert req.path == "/"
    assert req.method == HTTPMethod.GET
    assert req.headers == {}
    assert req.body is None
    assert req.to_dict()["path"] == "/"


def test_response():
    res = DummyResponse()

    assert res.status_code == 200
    assert res.body == {"ok": True}
    assert res.to_dict()["status_code"] == 200


def test_router():

    def handler():
        return "ok"

    router = DummyRouter()

    router.add_route(
        HTTPMethod.GET,
        "/",
        handler,
    )

    assert router.resolve(
        HTTPMethod.GET,
        "/",
    ) is handler


def test_server():
    server = DummyServer()

    response = server.handle(DummyRequest())

    assert response.status_code == 200


def test_request_is_abstract():
    with pytest.raises(TypeError):
        Request()


def test_response_is_abstract():
    with pytest.raises(TypeError):
        Response()


def test_router_is_abstract():
    with pytest.raises(TypeError):
        Router()


def test_server_is_abstract():
    with pytest.raises(TypeError):
        Server()