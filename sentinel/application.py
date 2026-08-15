"""
Application lifecycle for Sentinel OS.
"""

from __future__ import annotations

from sentinel.kernel.bootstrap import Bootstrap
from sentinel.kernel.kernel import Kernel


class Application:
    """
    Top-level Sentinel OS application.

    The application owns the process-level lifecycle while
    Bootstrap owns Kernel creation and shutdown.
    """

    def __init__(
        self,
        bootstrap: Bootstrap | None = None,
    ) -> None:
        self._bootstrap = (
            bootstrap
            if bootstrap is not None
            else Bootstrap()
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