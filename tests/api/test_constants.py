from sentinel.api.constants import (
    DEFAULT_API_VERSION,
    DEFAULT_HOST,
    DEFAULT_PORT,
    ContentType,
    HTTPMethod,
    HTTPStatus,
    ResponseStatus,
)


def test_defaults():
    assert DEFAULT_API_VERSION == "1.0.0"
    assert DEFAULT_HOST == "127.0.0.1"
    assert DEFAULT_PORT == 8000


def test_http_methods():
    assert HTTPMethod.GET.value == "GET"
    assert HTTPMethod.POST.value == "POST"
    assert HTTPMethod.PUT.value == "PUT"
    assert HTTPMethod.PATCH.value == "PATCH"
    assert HTTPMethod.DELETE.value == "DELETE"


def test_content_types():
    assert ContentType.JSON.value == "application/json"
    assert ContentType.TEXT.value == "text/plain"
    assert ContentType.HTML.value == "text/html"


def test_response_status():
    assert ResponseStatus.SUCCESS.value == "success"
    assert ResponseStatus.ERROR.value == "error"


def test_http_status():
    assert HTTPStatus.OK.value == 200
    assert HTTPStatus.CREATED.value == 201
    assert HTTPStatus.BAD_REQUEST.value == 400
    assert HTTPStatus.UNAUTHORIZED.value == 401
    assert HTTPStatus.FORBIDDEN.value == 403
    assert HTTPStatus.NOT_FOUND.value == 404
    assert HTTPStatus.INTERNAL_SERVER_ERROR.value == 500