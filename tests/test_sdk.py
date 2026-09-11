"""
Application SDK contract tests for Sentinel OS.
"""

from __future__ import annotations

from sentinel import Application
from sentinel.knowledge.document import Document
from sentinel.orchestration.models import OrchestrationRequest


def test_sdk_application_lifecycle() -> None:
    application = Application()

    assert application.running is False

    application.start()

    assert application.running is True
    assert application.health["healthy"] is True

    application.shutdown()

    assert application.running is False


def test_sdk_memory_workflow() -> None:
    with Application() as application:
        entry = application.memory.create(
            "sdk-memory",
            "Sentinel SDK test memory",
        )

        assert entry.id == "sdk-memory"
        assert application.memory.exists("sdk-memory") is True

        retrieved = application.memory.get("sdk-memory")

        assert retrieved.id == "sdk-memory"
        assert retrieved.content == "Sentinel SDK test memory"

        results = application.memory.search("SDK")

        assert len(results) == 1
        assert results[0].id == "sdk-memory"


def test_sdk_knowledge_workflow() -> None:
    with Application() as application:
        document = Document(
            id="sdk-document",
            text="Sentinel SDK knowledge test document.",
        )

        chunks = application.knowledge_runtime.add_document(
            document,
        )

        assert chunks

        results = application.knowledge_runtime.search(
            "Sentinel SDK",
        )

        assert results


def test_sdk_orchestration_can_execute() -> None:
    with Application() as application:
        request = OrchestrationRequest(
            "sdk-request",
            "hello",
        )

        assert application.orchestration.can_execute(
            request,
        ) is True


def test_sdk_runtime_access() -> None:
    with Application() as application:
        assert application.runtime.execution is application.execution
        assert (
            application.runtime.orchestration
            is application.orchestration
        )
        assert application.runtime.memory is application.memory
        assert (
            application.runtime.knowledge
            is application.knowledge_runtime
        )


def test_sdk_context_manager_stops_application() -> None:
    with Application() as application:
        assert application.running is True

    assert application.running is False