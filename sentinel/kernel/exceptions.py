"""
Kernel-specific exception hierarchy for Sentinel OS.
"""

from __future__ import annotations

from sentinel.core.exceptions import (
    AlreadyExistsError,
    NotFoundError,
    OperationError,
    SentinelError,
)


class KernelError(SentinelError):
    """Base class for all kernel exceptions."""


# ============================================================================
# Service Exceptions
# ============================================================================

class ServiceError(KernelError):
    """Base class for service-related exceptions."""


class DuplicateServiceError(ServiceError, AlreadyExistsError):
    """Raised when attempting to register a service twice."""


class ServiceNotFoundError(ServiceError, NotFoundError):
    """Raised when a requested service is not registered."""


class ServiceAlreadyRunningError(ServiceError, OperationError):
    """Raised when starting an already-running service."""


class ServiceNotRunningError(ServiceError, OperationError):
    """Raised when stopping a service that is not running."""


# ============================================================================
# Dependency Exceptions
# ============================================================================

class DependencyError(KernelError):
    """Base class for dependency-related exceptions."""


class DependencyNotFoundError(DependencyError, NotFoundError):
    """Raised when a required dependency cannot be found."""


class CircularDependencyError(DependencyError):
    """Raised when circular dependencies are detected."""


# ============================================================================
# Scheduler Exceptions
# ============================================================================

class SchedulerError(KernelError):
    """Base class for scheduler-related exceptions."""


class DuplicateTaskError(SchedulerError, AlreadyExistsError):
    """Raised when attempting to register a task twice."""


class TaskNotFoundError(SchedulerError, NotFoundError):
    """Raised when a scheduled task cannot be found."""