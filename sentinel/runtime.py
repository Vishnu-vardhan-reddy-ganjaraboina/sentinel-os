"""
Runtime composition for Sentinel OS.
"""

from __future__ import annotations

from pathlib import Path

from sentinel.capabilities.manager import CapabilityManager
from sentinel.execution.runtime import ExecutionRuntimeService
from sentinel.infrastructure.configuration import Configuration
from sentinel.kernel.service import Service
from sentinel.knowledge.knowledge_service import KnowledgeService
from sentinel.knowledge.persistent_vector_store import (
    PersistentVectorStore,
)
from sentinel.knowledge.runtime import KnowledgeRuntimeService
from sentinel.knowledge.vector_store import InMemoryVectorStore
from sentinel.knowledge.vector_store import VectorStore
from sentinel.memory.runtime import MemoryRuntimeService
from sentinel.memory.service import MemoryService
from sentinel.orchestration.runtime import OrchestrationRuntimeService
from sentinel.security.identity import SecurityIdentity
from sentinel.security.manager import SecurityManager
from sentinel.storage.backends.sqlite import SQLiteBackend


class Runtime:
    """
    Composed Sentinel runtime.

    Runtime owns the service graph produced by RuntimeComposer.
    Lifecycle remains owned by Bootstrap and Kernel.
    """

    def __init__(
        self,
        services: tuple[Service, ...],
    ) -> None:
        if not isinstance(services, tuple):
            raise TypeError(
                "services must be a tuple of Service instances."
            )

        if not all(
            isinstance(service, Service)
            for service in services
        ):
            raise TypeError(
                "services must contain only Service instances."
            )

        names = [
            service.name
            for service in services
        ]

        if len(names) != len(set(names)):
            raise ValueError(
                "Runtime service names must be unique."
            )

        self._services = services

    @property
    def services(self) -> tuple[Service, ...]:
        """Return the composed runtime services."""
        return self._services

    def get(
        self,
        name: str,
    ) -> Service:
        """
        Return a composed runtime service by name.

        Raises:
            TypeError:
                If name is not a string.
            ValueError:
                If name is empty.
            KeyError:
                If the service does not exist.
        """
        if not isinstance(name, str):
            raise TypeError("name must be a string.")

        name = name.strip()

        if not name:
            raise ValueError("name must not be empty.")

        for service in self._services:
            if service.name == name:
                return service

        raise KeyError(
            f"Service '{name}' is not registered."
        )

    def get_typed(
        self,
        name: str,
        service_type: type[Service],
    ) -> Service:
        """
        Return a composed service validated against an expected type.

        Raises:
            TypeError:
                If service_type is invalid or the service is not an
                instance of the requested type.
        """
        if not isinstance(service_type, type):
            raise TypeError(
                "service_type must be a type."
            )

        service = self.get(name)

        if not isinstance(service, service_type):
            raise TypeError(
                f"Service '{name}' is not an instance of "
                f"{service_type.__name__}."
            )

        return service

    @property
    def execution(self) -> ExecutionRuntimeService:
        """Return the Execution runtime service."""
        return self.get_typed(
            "execution",
            ExecutionRuntimeService,
        )

    @property
    def orchestration(self) -> OrchestrationRuntimeService:
        """Return the Orchestration runtime service."""
        return self.get_typed(
            "orchestration",
            OrchestrationRuntimeService,
        )

    @property
    def memory(self) -> MemoryRuntimeService:
        """Return the Memory runtime service."""
        return self.get_typed(
            "memory",
            MemoryRuntimeService,
        )

    @property
    def knowledge(self) -> KnowledgeRuntimeService:
        """Return the Knowledge runtime service."""
        return self.get_typed(
            "knowledge",
            KnowledgeRuntimeService,
        )

    def __iter__(self):
        """Iterate over the composed runtime services."""
        return iter(self._services)

    def __len__(self) -> int:
        """Return the number of composed runtime services."""
        return len(self._services)

    def __repr__(self) -> str:
        """Return a useful runtime representation."""
        names = ", ".join(
            service.name
            for service in self._services
        )
        return f"Runtime(services=({names}))"


class RuntimeComposer:
    """Construct and wire Sentinel Kernel runtime services."""

    def __init__(
        self,
        *,
        capabilities: CapabilityManager | None = None,
        security: SecurityManager | None = None,
        identity: SecurityIdentity | None = None,
        memory: MemoryService | None = None,
        knowledge: KnowledgeService | None = None,
        knowledge_vector_store: VectorStore | None = None,
        configuration: Configuration | None = None,
    ) -> None:
        self._capabilities = capabilities
        self._security = security
        self._identity = identity
        self._memory = memory
        self._knowledge = knowledge
        self._knowledge_vector_store = knowledge_vector_store
        self._configuration = configuration

    def compose(self) -> Runtime:
        """
        Construct the core Sentinel runtime.

        The returned Runtime contains the shared Memory and Knowledge
        dependencies used by the core runtime services.
        """
        shared_memory = (
            self._memory
            if self._memory is not None
            else MemoryService()
        )

        resolved_vector_store = (
            self._knowledge_vector_store
            if self._knowledge_vector_store is not None
            else self._create_knowledge_vector_store(
                self._configuration,
            )
        )

        knowledge_runtime = KnowledgeRuntimeService(
            knowledge=self._knowledge,
            vector_store=resolved_vector_store,
        )

        shared_knowledge = knowledge_runtime.knowledge

        services = (
            ExecutionRuntimeService(),
            OrchestrationRuntimeService(
                capabilities=self._capabilities,
                security=self._security,
                identity=self._identity,
                memory=shared_memory,
                knowledge=shared_knowledge,
            ),
            MemoryRuntimeService(
                memory=shared_memory,
            ),
            knowledge_runtime,
        )

        return Runtime(services)

    @staticmethod
    def _create_knowledge_vector_store(
        configuration: Configuration | None,
    ) -> VectorStore:
        """
        Create the configured Knowledge vector store.

        The default backend is in-memory.

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

            if not isinstance(
                database_path,
                (str, Path),
            ):
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