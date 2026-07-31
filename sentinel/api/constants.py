"""
Constants for the Sentinel API subsystem.
"""

from __future__ import annotations

from enum import Enum

DEFAULT_API_VERSION = "1.0.0"
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8000


class HTTPMethod(Enum):
    """
    Supported HTTP methods.
    """

    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"


class ContentType(Enum):
    """
    Supported content types.
    """

    JSON = "application/json"
    TEXT = "text/plain"
    HTML = "text/html"


class ResponseStatus(Enum):
    """
    API response status.
    """

    SUCCESS = "success"
    ERROR = "error"


class HTTPStatus(Enum):
    """
    Common HTTP status codes.
    """

    OK = 200
    CREATED = 201
    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    FORBIDDEN = 403
    NOT_FOUND = 404
    INTERNAL_SERVER_ERROR = 500