"""
Router implementation for the Sentinel API subsystem.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from sentinel.api.constants import HTTPMethod
from sentinel.api.exceptions import (
    MethodNotAllowedError,
    RouteNotFoundError,
)
from sentinel.api.interfaces import Router


class APIRouter(Router):
    """
    Stores and resolves API routes.
    """

    def __init__(self) -> None:
        self._routes: dict[
            tuple[HTTPMethod, str],
            Callable[..., Any],
        ] = {}

    def add_route(
        self,
        method: HTTPMethod,
        path: str,
        handler: Callable[..., Any],
    ) -> None:

        if not isinstance(method, HTTPMethod):
            raise MethodNotAllowedError("Invalid HTTP method.")

        if not path:
            raise ValueError("path cannot be empty")

        key = (method, path)

        if key in self._routes:
            raise ValueError(
                f"Route already exists: {method.value} {path}"
            )

        self._routes[key] = handler

    def resolve(
        self,
        method: HTTPMethod,
        path: str,
    ) -> Callable[..., Any]:

        if not isinstance(method, HTTPMethod):
            raise MethodNotAllowedError("Invalid HTTP method.")

        key = (method, path)

        if key not in self._routes:
            raise RouteNotFoundError(
                f"Route not found: {method.value} {path}"
            )

        return self._routes[key]

    @property
    def routes(
        self,
    ) -> dict[tuple[HTTPMethod, str], Callable[..., Any]]:
        return self._routes

    def clear(self) -> None:
        self._routes.clear()

    def __contains__(
        self,
        item: tuple[HTTPMethod, str],
    ) -> bool:
        return item in self._routes

    def __len__(self) -> int:
        return len(self._routes)