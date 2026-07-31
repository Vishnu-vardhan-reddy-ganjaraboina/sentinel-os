"""
Exceptions for the Sentinel API subsystem.
"""

from __future__ import annotations


class APIError(Exception):
    """
    Base exception for all API-related errors.
    """


class RequestError(APIError):
    """
    Raised when an API request is invalid.
    """


class ResponseError(APIError):
    """
    Raised when an API response cannot be generated.
    """


class RouteNotFoundError(APIError):
    """
    Raised when a route cannot be found.
    """


class MethodNotAllowedError(APIError):
    """
    Raised when an HTTP method is not supported.
    """


class ServerError(APIError):
    """
    Raised when the API server encounters an internal error.
    """