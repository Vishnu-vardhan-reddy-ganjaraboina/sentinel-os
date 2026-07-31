"""
Abstract interfaces for the Sentinel API subsystem.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any

from sentinel.api.constants import HTTPMethod


class Request(ABC):
    """
    Represents an incoming API request.
    """

    @property
    @abstractmethod
    def path(self) -> str:
        ...

    @property
    @abstractmethod
    def method(self) -> HTTPMethod:
        ...

    @property
    @abstractmethod
    def headers(self) -> dict[str, str]:
        ...

    @property
    @abstractmethod
    def body(self) -> Any:
        ...

    @abstractmethod
    def to_dict(self) -> dict[str, Any]:
        ...


class Response(ABC):
    """
    Represents an outgoing API response.
    """

    @property
    @abstractmethod
    def status_code(self) -> int:
        ...

    @property
    @abstractmethod
    def headers(self) -> dict[str, str]:
        ...

    @property
    @abstractmethod
    def body(self) -> Any:
        ...

    @abstractmethod
    def to_dict(self) -> dict[str, Any]:
        ...


class Router(ABC):
    """
    Maps routes to handlers.
    """

    @abstractmethod
    def add_route(
        self,
        method: HTTPMethod,
        path: str,
        handler: Callable[..., Any],
    ) -> None:
        ...

    @abstractmethod
    def resolve(
        self,
        method: HTTPMethod,
        path: str,
    ) -> Callable[..., Any]:
        ...


class Server(ABC):
    """
    Base API server.
    """

    @abstractmethod
    def handle(
        self,
        request: Request,
    ) -> Response:
        ...