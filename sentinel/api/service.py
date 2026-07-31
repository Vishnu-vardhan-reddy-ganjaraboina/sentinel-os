"""
Service layer for the Sentinel API subsystem.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from sentinel.api.constants import HTTPMethod
from sentinel.api.interfaces import Request, Response
from sentinel.api.manager import APIManager


class APIService:
    """
    Public service interface for the API subsystem.
    """

    def __init__(
        self,
        manager: APIManager | None = None,
    ) -> None:

        self._manager = (
            manager
            if manager is not None
            else APIManager()
        )

    @property
    def manager(self) -> APIManager:
        return self._manager

    def add_route(
        self,
        method: HTTPMethod,
        path: str,
        handler: Callable[..., Any],
    ) -> None:
        self._manager.add_route(
            method,
            path,
            handler,
        )

    def handle(
        self,
        request: Request,
    ) -> Response:
        return self._manager.handle(request)

    def clear(self) -> None:
        self._manager.clear()

    def __len__(self) -> int:
        return len(self._manager)