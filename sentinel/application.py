"""
Application lifecycle for Sentinel OS.
"""

from __future__ import annotations

from pathlib import Path

from sentinel.capabilities.manager import CapabilityManager
from sentinel.execution.runtime import ExecutionRuntimeService
from sentinel.infrastructure.configuration import Configuration
from sentinel.kernel.bootstrap import Bootstrap
from sentinel.kernel.kernel import Kernel
from sentinel.knowledge.knowledge_service import KnowledgeService
from sentinel.knowledge.persistent_vector_store import (
    PersistentVectorStore,
)
from sentinel.knowledge.runtime import KnowledgeRuntimeService
from sentinel.knowledge.vector_store import (
    InMemoryVectorStore,
    VectorStore,
)
from sentinel.memory.runtime import MemoryRuntimeService
from sentinel.memory.service import MemoryService
from sentinel.orchestration.runtime import OrchestrationRuntimeService
from sentinel.security.identity import SecurityIdentity
from sentinel.security.manager import SecurityManager
from sentinel.storage.backends.sqlite import SQLiteBackend


class Application:
    """
    Top-level Sentinel OS application.

    The application owns the process-level lifecycle while
    Bootstrap owns Kernel creation and shutdown.

    Dependencies can be explicitly injected for tests and advanced
    deployments. Configuration can also be supplied to construct
    production infrastructure automatically.
    """

    def __init__(
        self,
        bootstrap: Bootstrap | None = None,
        *,
        capabilities: CapabilityManager | None = None,
        security: SecurityManager | None = None,
        identity: SecurityIdentity | None = None,
        memory: MemoryService | None = None,
        knowledge: KnowledgeService | None = None,
        knowledge_vector_store: VectorStore | None = None,
        configuration: Configuration | None = None,
    ) -> None:
        if bootstrap is not None:
            self._bootstrap = bootstrap
        else:
            shared_memory = (
                memory
                if memory is not None
                else MemoryService()
            )

            resolved_vector_store = (
                knowledge_vector_store
                if knowledge_vector_store is not None
                else self._create_knowledge_vector_store(
                    configuration,
                )
            )

            knowledge_runtime = KnowledgeRuntimeService(
                knowledge=knowledge,
                vector_store=resolved_vector_store,
            )

            shared_knowledge = knowledge_runtime.knowledge

            self._bootstrap = Bootstrap(
                services=(
                    ExecutionRuntimeService(),

                    OrchestrationRuntimeService(
                        capabilities=capabilities,
                        security=security,
                        identity=identity,
                        memory=shared_memory,
                        knowledge=shared_knowledge,
                    ),

                    MemoryRuntimeService(
                        memory=shared_memory,
                    ),

                    knowledge_runtime,
                ),
            )

        self._running = False

    @staticmethod
    def _create_knowledge_vector_store(
        configuration: Configuration | None,
    ) -> VectorStore:
        """
        Create the configured Knowledge vector store.

        The default remains the in-memory implementation.

        Supported configuration:

            knowledge:
                backend: memory

        or:

            knowledge:
                backend: sqlite
                database_path: data/sentinel-knowledge.db
        """
        if configuration is None:
            return InMemoryVectorStore()

        backend = str(
            configuration.get(
                "knowledge.backend",
                "memory",
            )
        ).strip().lower()

        if backend == "memory":
            return InMemoryVectorStore()

        if backend == "sqlite":
            database_path = configuration.get(
                "knowledge.database_path",
                "data/sentinel-knowledge.db",
            )

            if not isinstance(database_path, (str, Path)):
                raise ValueError(
                    "knowledge.database_path must be a string or path."
                )

            return PersistentVectorStore(
                backend=SQLiteBackend(
                    Path(database_path),
                ),
            )

        raise ValueError(
            f"Unsupported knowledge backend: '{backend}'."
        )

    @property
    def bootstrap(self) -> Bootstrap:
        """Return the application bootstrap."""
        return self._bootstrap

    @property
    def kernel(self) -> Kernel:
        """
        Return the running Kernel.

        Raises:
            RuntimeError:
                If the application has not been started.
        """
        return self._bootstrap.kernel

    @property
    def running(self) -> bool:
        """Return whether the application is running."""
        return self._running

    def start(self) -> Kernel:
        """
        Start Sentinel OS.

        Returns:
            Kernel:
                The running Kernel instance.

        Raises:
            RuntimeError:
                If the application is already running.
        """
        if self._running:
            raise RuntimeError(
                "Sentinel application is already running."
            )

        kernel = self._bootstrap.start()
        self._running = True

        return kernel

    def shutdown(self) -> None:
        """
        Shut down Sentinel OS.

        Raises:
            RuntimeError:
                If the application is not running.
        """
        if not self._running:
            raise RuntimeError(
                "Sentinel application is not running."
            )

        self._bootstrap.shutdown()
        self._running = False

    def __enter__(self) -> Application:
        self.start()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: object | None,
    ) -> None:
        self.shutdown()
    
    @property
    def knowledge(self) -> KnowledgeService:
        """
        Return the application's Knowledge service.

        Raises:
            RuntimeError:
                If the application has not been started.
            TypeError:
                If the registered Knowledge service has an
                unexpected type.
        """
        runtime = self.kernel.get_typed(
            "knowledge",
            KnowledgeRuntimeService,
        )

        return runtime.knowledge