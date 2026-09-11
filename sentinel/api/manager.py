"""
Manager for the Sentinel API subsystem.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from sentinel.api.constants import HTTPMethod
from sentinel.api.interfaces import Request, Response
from sentinel.api.router import APIRouter
from sentinel.api.server import APIServer


class APIManager:
    """
    Coordinates the API router and server.
    """

    def __init__(
        self,
        router: APIRouter | None = None,
        server: APIServer | None = None,
    ) -> None:

        if router is not None and not isinstance(router, APIRouter):
            raise TypeError("router must be an APIRouter")

        if server is not None and not isinstance(server, APIServer):
            raise TypeError("server must be an APIServer")

        self._router = router if router is not None else APIRouter()

        if server is not None:
            if server.router is not self._router:
                raise ValueError(
                    "server must use the same router as the manager"
                )
            self._server = server
        else:
            self._server = APIServer(self._router)

    @property
    def router(self) -> APIRouter:
        return self._router

    @property
    def server(self) -> APIServer:
        return self._server

    def add_route(
        self,
        method: HTTPMethod,
        path: str,
        handler: Callable[..., Any],
    ) -> None:
        self._router.add_route(
            method,
            path,
            handler,
        )

    def handle(
        self,
        request: Request,
    ) -> Response:
        return self._server.handle(request)

    def clear(self) -> None:
        self._router.clear()

    def __len__(self) -> int:
        return len(self._router)
