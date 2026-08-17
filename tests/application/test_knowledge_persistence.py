"""
Application-level tests for persistent Knowledge storage.
"""

from pathlib import Path

from sentinel.application import Application
from sentinel.knowledge.document import Document
from sentinel.knowledge.persistent_vector_store import (
    PersistentVectorStore,
)
from sentinel.storage.backends.sqlite import SQLiteBackend


def create_persistent_store(
    database: Path,
) -> PersistentVectorStore:
    """
    Create a SQLite-backed persistent vector store.
    """
    backend = SQLiteBackend(database)

    return PersistentVectorStore(
        backend=backend,
    )


def test_application_uses_persistent_knowledge(
    tmp_path: Path,
) -> None:
    database = tmp_path / "sentinel-knowledge.db"

    store = create_persistent_store(database)

    application = Application(
        knowledge_vector_store=store,
    )

    try:
        kernel = application.start()

        knowledge_runtime = kernel.get("knowledge")

        assert knowledge_runtime is not None
        assert kernel.running("knowledge") is True

        knowledge = knowledge_runtime.knowledge

        chunks = knowledge.add_document(
            Document(
                id="doc.persistence",
                text="Sentinel persistent knowledge",
            )
        )

        assert len(chunks) == 1

        results = knowledge.search(
            "Sentinel persistent knowledge",
        )

        assert len(results) == 1
        assert results[0].document_id == "doc.persistence"

    finally:
        application.shutdown()


def test_knowledge_survives_application_restart(
    tmp_path: Path,
) -> None:
    database = tmp_path / "sentinel-restart.db"

    first_store = create_persistent_store(database)

    first_application = Application(
        knowledge_vector_store=first_store,
    )

    try:
        first_kernel = first_application.start()

        first_knowledge_runtime = first_kernel.get(
            "knowledge",
        )

        assert first_knowledge_runtime is not None

        first_knowledge = first_knowledge_runtime.knowledge

        first_knowledge.add_document(
            Document(
                id="doc.restart",
                text="Knowledge survives application restart",
            )
        )

    finally:
        first_application.shutdown()

    second_store = create_persistent_store(database)

    second_application = Application(
        knowledge_vector_store=second_store,
    )

    try:
        second_kernel = second_application.start()

        second_knowledge_runtime = second_kernel.get(
            "knowledge",
        )

        assert second_knowledge_runtime is not None

        second_knowledge = second_knowledge_runtime.knowledge

        results = second_knowledge.search(
            "Knowledge survives application restart",
        )

        assert len(results) == 1
        assert results[0].id.startswith(
            "doc.restart",
        )
        assert results[0].document_id == "doc.restart"

    finally:
        second_application.shutdown()