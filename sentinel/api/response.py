"""
Response model for the Sentinel API subsystem.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from sentinel.api.constants import (
    ContentType,
    HTTPStatus,
)
from sentinel.api.interfaces import Response


class APIResponse(Response):
    """
    Concrete implementation of an API response.
    """

    def __init__(
        self,
        status_code: HTTPStatus = HTTPStatus.OK,
        body: Any = None,
        headers: dict[str, str] | None = None,
    ) -> None:

        if not isinstance(status_code, HTTPStatus):
            raise TypeError("status_code must be an HTTPStatus")

        if headers is not None:
            if not isinstance(headers, dict):
                raise TypeError("headers must be a dictionary")

            if not all(
                isinstance(key, str) and isinstance(value, str)
                for key, value in headers.items()
            ):
                raise TypeError("headers must contain string keys and values")

        self._status_code = status_code.value
        self._body = deepcopy(body)
        self._headers = deepcopy(headers) if headers is not None else {}

        self._headers.setdefault(
            "Content-Type",
            ContentType.JSON.value,
        )

    @property
    def status_code(self) -> int:
        return self._status_code

    @property
    def headers(self) -> dict[str, str]:
        return deepcopy(self._headers)

    @property
    def body(self) -> Any:
        return deepcopy(self._body)

    def to_dict(self) -> dict[str, Any]:
        return {
            "status_code": self.status_code,
            "headers": self.headers,
            "body": self.body,
        }

    def __repr__(self) -> str:
        return (
            f"APIResponse("
            f"status_code={self.status_code})"
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, APIResponse):
            return False

        return (
            self.status_code == other.status_code
            and self.headers == other.headers
            and self.body == other.body
        )

    def __hash__(self) -> int:
        return hash(
            (
                self.status_code,
                tuple(sorted(self.headers.items())),
                repr(self.body),
            )
        )
