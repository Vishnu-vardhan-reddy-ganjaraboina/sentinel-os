"""
Application lifecycle for Sentinel OS.
"""

from __future__ import annotations

from collections.abc import Mapping
from threading import RLock
from typing import Any

from sentinel.capabilities.manager import CapabilityManager
from sentinel.execution.runtime import ExecutionRuntimeService
from sentinel.infrastructure.configuration import Configuration
from sentinel.kernel.bootstrap import Bootstrap
from sentinel.kernel.kernel import Kernel
from sentinel.knowledge.knowledge_service import KnowledgeService
from sentinel.knowledge.runtime import KnowledgeRuntimeService
from sentinel.knowledge.vector_store import VectorStore
from sentinel.memory.runtime import MemoryRuntimeService
from sentinel.memory.service import MemoryService
from sentinel.orchestration.runtime import OrchestrationRuntimeService
from sentinel.runtime import Runtime, RuntimeComposer
from sentinel.security.identity import SecurityIdentity
from sentinel.security.manager import SecurityManager


class Application:
    """
    Top-level Sentinel OS application.

    The application owns the process-level lifecycle while
    Bootstrap owns Kernel creation and shutdown.

    Runtime owns the composed runtime service graph.

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
        self._runtime: Runtime | None = None

        if bootstrap is not None:
            self._bootstrap = bootstrap
        else:
            if configuration is not None:
                configuration.validate()

            self._runtime = RuntimeComposer(
                capabilities=capabilities,
                security=security,
                identity=identity,
                memory=memory,
                knowledge=knowledge,
                knowledge_vector_store=knowledge_vector_store,
                configuration=configuration,
            ).compose()

            self._bootstrap = Bootstrap(
                services=self._runtime.services,
            )

        self._running = False
        self._lock = RLock()

    @property
    def bootstrap(self) -> Bootstrap:
        """Return the application bootstrap."""
        return self._bootstrap

    @property
    def runtime(self) -> Runtime:
        """
        Return the composed runtime.

        Raises:
            RuntimeError:
                If the application uses an externally supplied
                Bootstrap and therefore has no composed Runtime.
        """
        if self._runtime is None:
            raise RuntimeError(
                "Runtime is not available for an externally supplied "
                "bootstrap."
            )

        return self._runtime

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
        with self._lock:
            return self._running

    @property
    def execution(self) -> ExecutionRuntimeService:
        """
        Return the application's Execution runtime service.

        Raises:
            RuntimeError:
                If no composed Runtime is available.
        """
        return self.runtime.execution

    @property
    def orchestration(self) -> OrchestrationRuntimeService:
        """
        Return the application's Orchestration runtime service.

        Raises:
            RuntimeError:
                If no composed Runtime is available.
        """
        return self.runtime.orchestration

    @property
    def memory(self) -> MemoryRuntimeService:
        """
        Return the application's Memory runtime service.

        Raises:
            RuntimeError:
                If no composed Runtime is available.
        """
        return self.runtime.memory

    @property
    def knowledge_runtime(self) -> KnowledgeRuntimeService:
        """
        Return the application's Knowledge runtime service.

        Raises:
            RuntimeError:
                If no composed Runtime is available.
        """
        return self.runtime.knowledge

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
        with self._lock:
            if self._running:
                raise RuntimeError(
                    "Sentinel application is already running."
                )

        kernel = self._bootstrap.start()

        with self._lock:
            self._running = True

        return kernel

    def shutdown(self) -> None:
        """
        Shut down Sentinel OS.

        Raises:
            RuntimeError:
                If the application is not running.
        """
        with self._lock:
            if not self._running:
                raise RuntimeError(
                    "Sentinel application is not running."
                )

        self._bootstrap.shutdown()

        with self._lock:
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
                If no composed Runtime is available.
            TypeError:
                If the runtime Knowledge service has an
                unexpected type.
        """
        return self.knowledge_runtime.knowledge

    @property
    def health(self) -> Mapping[str, Any]:
        """
        Return application-wide health information.

        Raises:
            RuntimeError:
                If the application has not been started.
        """
        if not self.running:
            raise RuntimeError(
                "Sentinel application is not running."
            )

        return self.kernel.health()