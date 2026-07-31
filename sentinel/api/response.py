"""
Response model for the Sentinel API subsystem.
"""

from __future__ import annotations

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

        self._status_code = status_code.value
        self._body = body
        self._headers = headers.copy() if headers else {}

        self._headers.setdefault(
            "Content-Type",
            ContentType.JSON.value,
        )

    @property
    def status_code(self) -> int:
        return self._status_code

    @property
    def headers(self) -> dict[str, str]:
        return self._headers

    @property
    def body(self) -> Any:
        return self._body

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