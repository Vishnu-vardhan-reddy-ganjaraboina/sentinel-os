"""
Application configuration integration tests.
"""

from pathlib import Path

import pytest

from sentinel.application import Application
from sentinel.core.exceptions import ConfigurationError
from sentinel.infrastructure.configuration import Configuration
from sentinel.knowledge.persistent_vector_store import (
    PersistentVectorStore,
)
from sentinel.knowledge.vector_store import InMemoryVectorStore


def create_configuration(
    backend: str,
    database_path: str | None = None,
) -> Configuration:
    """
    Create Knowledge configuration for testing.
    """
    knowledge: dict[str, object] = {
        "backend": backend,
    }

    if database_path is not None:
        knowledge["database_path"] = database_path

    return Configuration.from_dict(
        {
            "knowledge": knowledge,
        }
    )


def test_default_application_uses_in_memory_knowledge() -> None:
    application = Application()

    application.start()

    try:
        assert isinstance(
            application.knowledge.retriever.vector_store,
            InMemoryVectorStore,
        )
    finally:
        application.shutdown()


def test_memory_backend_uses_in_memory_vector_store() -> None:
    configuration = create_configuration("memory")

    application = Application(
        configuration=configuration,
    )

    application.start()

    try:
        assert isinstance(
            application.knowledge.retriever.vector_store,
            InMemoryVectorStore,
        )
    finally:
        application.shutdown()


def test_sqlite_backend_uses_persistent_vector_store(
    tmp_path: Path,
) -> None:
    database = tmp_path / "configured.db"

    configuration = create_configuration(
        "sqlite",
        str(database),
    )

    application = Application(
        configuration=configuration,
    )

    application.start()

    try:
        assert isinstance(
            application.knowledge.retriever.vector_store,
            PersistentVectorStore,
        )
    finally:
        application.shutdown()


def test_application_rejects_invalid_configuration() -> None:
    configuration = Configuration.from_dict(
        {
            "knowledge": {
                "backend": "unsupported",
            },
        }
    )

    with pytest.raises(
        ConfigurationError,
        match="Unsupported knowledge backend",
    ):
        Application(
            configuration=configuration,
        )