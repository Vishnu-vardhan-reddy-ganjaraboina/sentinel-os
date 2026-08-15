from typing import cast

from sentinel.application import Application
from sentinel.knowledge.document import Document
from sentinel.knowledge.runtime import KnowledgeRuntimeService
from sentinel.orchestration.runtime import OrchestrationRuntimeService


def test_application_knowledge_service_is_registered() -> None:
    application = Application()

    try:
        kernel = application.start()

        knowledge_service = cast(
            KnowledgeRuntimeService,
            kernel.get("knowledge"),
        )

        assert knowledge_service.knowledge is not None

    finally:
        application.shutdown()


def test_application_orchestration_uses_shared_knowledge() -> None:
    application = Application()

    try:
        kernel = application.start()

        orchestration_service = cast(
            OrchestrationRuntimeService,
            kernel.get("orchestration"),
        )

        knowledge_service = cast(
            KnowledgeRuntimeService,
            kernel.get("knowledge"),
        )

        orchestration = orchestration_service.orchestration
        knowledge = knowledge_service.knowledge

        assert orchestration.knowledge is knowledge

    finally:
        application.shutdown()


def test_application_knowledge_can_index_and_search() -> None:
    application = Application()

    try:
        kernel = application.start()

        knowledge_service = cast(
            KnowledgeRuntimeService,
            kernel.get("knowledge"),
        )

        knowledge = knowledge_service.knowledge

        knowledge.add_document(
            Document(
                id="integration.sentinel",
                text="Sentinel OS orchestration uses controlled capabilities.",
            )
        )

        results = knowledge.search("Sentinel OS")

        assert len(results) == 1
        assert results[0].document_id == "integration.sentinel"

    finally:
        application.shutdown()
