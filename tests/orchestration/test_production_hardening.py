"""
Production hardening tests for the Sentinel Orchestration subsystem.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from time import sleep

import pytest

from sentinel.orchestration.exceptions import (
    OrchestrationExecutionError,
    OrchestrationValidationError,
)
from sentinel.orchestration.manager import OrchestrationManager
from sentinel.orchestration.models import OrchestrationRequest
from sentinel.orchestration.runtime import OrchestrationRuntimeService
from sentinel.orchestration.service import OrchestrationService


def test_manager_rejects_non_request() -> None:
    manager = OrchestrationManager()

    with pytest.raises(TypeError):
        manager.execute("not-a-request")  # type: ignore[arg-type]


def test_manager_rejects_empty_input() -> None:
    manager = OrchestrationManager()

    request = OrchestrationRequest(
        request_id="request.empty-input",
        input="   ",
    )

    with pytest.raises(OrchestrationValidationError):
        manager.execute(request)


def test_can_execute_invalid_input_returns_false() -> None:
    manager = OrchestrationManager()

    request = OrchestrationRequest(
        request_id="request.invalid-input",
        input="   ",
    )

    assert manager.can_execute(request) is False


def test_concurrent_different_requests_are_allowed() -> None:
    barrier = Barrier(2)

    def handler(request: OrchestrationRequest) -> str:
        barrier.wait(timeout=5)
        return request.id

    manager = OrchestrationManager(handler=handler)

    requests = [
        OrchestrationRequest(
            request_id="request.concurrent.1",
            input="one",
        ),
        OrchestrationRequest(
            request_id="request.concurrent.2",
            input="two",
        ),
    ]

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [
            executor.submit(manager.execute, request)
            for request in requests
        ]

        results = [future.result(timeout=10) for future in futures]

    assert {result.request_id for result in results} == {
        "request.concurrent.1",
        "request.concurrent.2",
    }


def test_same_request_id_is_serialized() -> None:
    active = 0
    maximum_active = 0

    from threading import Lock

    state_lock = Lock()

    def handler(request: OrchestrationRequest) -> str:
        nonlocal active, maximum_active

        with state_lock:
            active += 1
            maximum_active = max(maximum_active, active)

        sleep(0.05)

        with state_lock:
            active -= 1

        return request.id

    manager = OrchestrationManager(handler=handler)

    requests = [
        OrchestrationRequest(
            request_id="request.same",
            input="same",
        )
        for _ in range(4)
    ]

    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = [
            executor.submit(manager.execute, request)
            for request in requests
        ]

        results = [future.result(timeout=10) for future in futures]

    assert len(results) == 4
    assert all(result.success for result in results)
    assert maximum_active == 1


def test_same_request_id_persistence_is_stable() -> None:
    counter = 0
    counter_lock = __import__("threading").Lock()

    def handler(request: OrchestrationRequest) -> dict[str, int]:
        nonlocal counter

        with counter_lock:
            counter += 1
            value = counter

        return {"value": value}

    manager = OrchestrationManager(handler=handler)

    requests = [
        OrchestrationRequest(
            request_id="request.persistence",
            input="hello",
        )
        for _ in range(8)
    ]

    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = [
            executor.submit(manager.execute, request)
            for request in requests
        ]

        results = [future.result(timeout=10) for future in futures]

    memory = manager.memory.get("orchestration:request.persistence")

    assert memory is not None
    assert memory.content == results[-1].to_dict() or any(
        memory.content == result.to_dict()
        for result in results
    )


def test_brain_invalid_result_is_rejected() -> None:
    class BrokenBrain:
        def create_context(
            self,
            context_id: str,
            **data: object,
        ) -> object:
            return object()

        def execute(
            self,
            request: str,
            context: object,
        ) -> object:
            return "invalid"

    manager = OrchestrationManager(
        brain=BrokenBrain(),  # type: ignore[arg-type]
    )

    request = OrchestrationRequest(
        request_id="request.invalid-brain",
        input="hello",
    )

    with pytest.raises(OrchestrationExecutionError):
        manager.execute(request)


def test_runtime_lifecycle_is_thread_safe() -> None:
    runtime = OrchestrationRuntimeService()

    def initialize_and_shutdown() -> None:
        runtime.initialize()
        runtime.shutdown()

    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = [
            executor.submit(initialize_and_shutdown)
            for _ in range(20)
        ]

        for future in futures:
            future.result(timeout=10)

    assert runtime.health() == {
        "healthy": False,
    }


def test_runtime_concurrent_initialize_is_safe() -> None:
    runtime = OrchestrationRuntimeService()

    barrier = Barrier(8)

    def initialize() -> None:
        barrier.wait(timeout=5)
        runtime.initialize()

    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = [
            executor.submit(initialize)
            for _ in range(8)
        ]

        for future in futures:
            future.result(timeout=10)

    assert runtime.health() == {
        "healthy": True,
    }


def test_runtime_concurrent_shutdown_is_safe() -> None:
    runtime = OrchestrationRuntimeService()
    runtime.initialize()

    barrier = Barrier(8)

    def shutdown() -> None:
        barrier.wait(timeout=5)
        runtime.shutdown()

    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = [
            executor.submit(shutdown)
            for _ in range(8)
        ]

        for future in futures:
            future.result(timeout=10)

    assert runtime.health() == {
        "healthy": False,
    }


def test_service_remains_thin_facade() -> None:
    manager = OrchestrationManager(
        handler=lambda request: {"request": request.input},
    )

    service = OrchestrationService(manager=manager)

    request = OrchestrationRequest(
        request_id="request.facade",
        input="hello",
    )

    result = service.execute(request)

    assert result.success is True
    assert result.data == {
        "request": "hello",
    }


def test_request_lock_registry_is_cleaned_after_execution() -> None:
    manager = OrchestrationManager(
        handler=lambda request: request.id,
    )

    request = OrchestrationRequest(
        request_id="request.cleanup",
        input="hello",
    )

    manager.execute(request)

    assert manager._request_locks == {}
