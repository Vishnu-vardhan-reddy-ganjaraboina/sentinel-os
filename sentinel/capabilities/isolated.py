"""Capability adapter that executes its implementation in a worker process."""

from __future__ import annotations

from typing import Any

from sentinel.capabilities.capability import BaseCapability
from sentinel.capabilities.metadata import CapabilityMetadata
from sentinel.execution.isolated_worker import IsolatedWorker


class IsolatedCapability(BaseCapability):
    """A capability whose implementation is an allowlisted importable function.

    The callable receives capability keyword arguments in a disposable worker.
    Capability metadata and enable/disable admission remain in the parent.
    """

    def __init__(
        self,
        metadata: CapabilityMetadata,
        *,
        worker: IsolatedWorker,
        callable_ref: str,
        timeout: float = 30.0,
    ) -> None:
        if not isinstance(worker, IsolatedWorker):
            raise TypeError("worker must be an IsolatedWorker.")
        if not isinstance(callable_ref, str) or ":" not in callable_ref:
            raise ValueError("callable_ref must use 'module:qualified_name'.")
        if timeout <= 0:
            raise ValueError("timeout must be greater than zero.")
        super().__init__(metadata)
        self._worker = worker
        self._callable_ref = callable_ref
        self._timeout = timeout

    def run(self, **kwargs: Any) -> Any:
        """Run the capability in a disposable isolated worker."""
        return self._worker.execute(
            self._callable_ref,
            timeout=self._timeout,
            **kwargs,
        )
