"""
Server implementation for the Sentinel API subsystem.
"""

from __future__ import annotations

from sentinel.api.constants import (
    HTTPStatus,
    ResponseStatus,
)
from sentinel.api.exceptions import (
    MethodNotAllowedError,
    RouteNotFoundError,
)
from sentinel.api.interfaces import (
    Request,
    Response,
    Server,
)
from sentinel.api.response import APIResponse
from sentinel.api.router import APIRouter


class APIServer(Server):
    """
    Simple API server that dispatches requests to registered handlers.
    """

    def __init__(self, router: APIRouter | None = None) -> None:
        if router is None:
            self._router = APIRouter()
        else:
            self._router = router

    @property
    def router(self) -> APIRouter:
        return self._router

    def handle(self, request: Request) -> Response:
        try:
            handler = self._router.resolve(
                request.method,
                request.path,
            )

            result = handler(request)

            if isinstance(result, APIResponse):
                return result

            return APIResponse(
                status_code=HTTPStatus.OK,
                body={
                    "status": ResponseStatus.SUCCESS.value,
                    "data": result,
                },
            )

        except (RouteNotFoundError, MethodNotAllowedError) as exc:
            return APIResponse(
                status_code=HTTPStatus.NOT_FOUND,
                body={
                    "status": ResponseStatus.ERROR.value,
                    "message": str(exc),
                },
            )

        except Exception as exc:
            return APIResponse(
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                body={
                    "status": ResponseStatus.ERROR.value,
                    "message": str(exc),
                },
            )