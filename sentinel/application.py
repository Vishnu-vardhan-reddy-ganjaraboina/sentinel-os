"""
Application lifecycle for Sentinel OS.
"""

from __future__ import annotations

from sentinel.capabilities.manager import CapabilityManager
from sentinel.execution.runtime import ExecutionRuntimeService
from sentinel.kernel.bootstrap import Bootstrap
from sentinel.kernel.kernel import Kernel
from sentinel.knowledge.knowledge_service import KnowledgeService
from sentinel.knowledge.runtime import KnowledgeRuntimeService
from sentinel.knowledge.vector_store import VectorStore
from sentinel.memory.runtime import MemoryRuntimeService
from sentinel.memory.service import MemoryService
from sentinel.orchestration.runtime import OrchestrationRuntimeService
from sentinel.security.identity import SecurityIdentity
from sentinel.security.manager import SecurityManager


class Application:
    """
    Top-level Sentinel OS application.

    The application owns the process-level lifecycle while
    Bootstrap owns Kernel creation and shutdown.
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
    ) -> None:
        if bootstrap is not None:
            self._bootstrap = bootstrap
        else:
            shared_memory = (
                memory
                if memory is not None
                else MemoryService()
            )

            knowledge_runtime = KnowledgeRuntimeService(
                knowledge=knowledge,
                vector_store=knowledge_vector_store,
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
