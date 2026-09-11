"""
Router implementation for the Sentinel API subsystem.
"""

from __future__ import annotations

from collections.abc import Callable
from threading import RLock
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
        self._lock = RLock()

    def add_route(
        self,
        method: HTTPMethod,
        path: str,
        handler: Callable[..., Any],
    ) -> None:

        if not isinstance(method, HTTPMethod):
            raise MethodNotAllowedError("Invalid HTTP method.")

        if not isinstance(path, str):
            raise TypeError("path must be a string")

        if not path.strip():
            raise ValueError("path cannot be empty")

        if not callable(handler):
            raise TypeError("handler must be callable")

        key = (method, path)

        with self._lock:
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

        if not isinstance(path, str):
            raise TypeError("path must be a string")

        with self._lock:
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
        with self._lock:
            return dict(self._routes)

    def clear(self) -> None:
        with self._lock:
            self._routes.clear()

    def __contains__(
        self,
        item: tuple[HTTPMethod, str],
    ) -> bool:
        with self._lock:
            return item in self._routes

    def __len__(self) -> int:
        with self._lock:
            return len(self._routes)
