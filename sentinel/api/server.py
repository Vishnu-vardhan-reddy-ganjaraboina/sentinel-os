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
    RequestError,
    RouteNotFoundError,
    ServerError,
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
        self._router = router if router is not None else APIRouter()

    @property
    def router(self) -> APIRouter:
        return self._router

    def handle(self, request: Request) -> Response:
        try:
            self._validate_request(request)

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

        except RouteNotFoundError as exc:
            return self._error_response(
                HTTPStatus.NOT_FOUND,
                str(exc),
            )

        except MethodNotAllowedError as exc:
            return self._error_response(
                HTTPStatus.METHOD_NOT_ALLOWED,
                str(exc),
            )

        except RequestError as exc:
            return self._error_response(
                HTTPStatus.BAD_REQUEST,
                str(exc),
            )

        except ServerError as exc:
            return self._error_response(
                HTTPStatus.INTERNAL_SERVER_ERROR,
                str(exc),
            )

        except Exception:
            return self._error_response(
                HTTPStatus.INTERNAL_SERVER_ERROR,
                "Internal server error.",
            )

    @staticmethod
    def _validate_request(request: Request) -> None:
        if not isinstance(request, Request):
            raise RequestError("Invalid API request.")

        if not request.path:
            raise RequestError("Request path cannot be empty.")

    @staticmethod
    def _error_response(
        status_code: HTTPStatus,
        message: str,
    ) -> APIResponse:
        return APIResponse(
            status_code=status_code,
            body={
                "status": ResponseStatus.ERROR.value,
                "message": message,
            },
        )
