"""
Request model for the Sentinel API subsystem.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from sentinel.api.constants import HTTPMethod
from sentinel.api.interfaces import Request


class APIRequest(Request):
    """
    Concrete implementation of an API request.
    """

    def __init__(
        self,
        path: str,
        method: HTTPMethod,
        headers: dict[str, str] | None = None,
        body: Any = None,
    ) -> None:

        if not isinstance(path, str):
            raise TypeError("path must be a string")

        if not path.strip():
            raise ValueError("path cannot be empty")

        if not isinstance(method, HTTPMethod):
            raise TypeError("method must be an HTTPMethod")

        if headers is not None:
            if not isinstance(headers, dict):
                raise TypeError("headers must be a dictionary")

            if not all(
                isinstance(key, str) and isinstance(value, str)
                for key, value in headers.items()
            ):
                raise TypeError("headers must contain string keys and values")

        self._path = path
        self._method = method
        self._headers = deepcopy(headers) if headers is not None else {}
        self._body = deepcopy(body)

    @property
    def path(self) -> str:
        return self._path

    @property
    def method(self) -> HTTPMethod:
        return self._method

    @property
    def headers(self) -> dict[str, str]:
        return deepcopy(self._headers)

    @property
    def body(self) -> Any:
        return deepcopy(self._body)

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "method": self.method.value,
            "headers": self.headers,
            "body": self.body,
        }

    def __repr__(self) -> str:
        return (
            f"APIRequest("
            f"path={self.path!r}, "
            f"method={self.method.value!r})"
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, APIRequest):
            return False

        return (
            self.path == other.path
            and self.method == other.method
            and self.headers == other.headers
            and self.body == other.body
        )

    def __hash__(self) -> int:
        return hash(
            (
                self.path,
                self.method,
                tuple(sorted(self.headers.items())),
                repr(self.body),
            )
        )
