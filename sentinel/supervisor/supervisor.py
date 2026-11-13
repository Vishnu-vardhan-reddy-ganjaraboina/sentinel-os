from __future__ import annotations

from threading import RLock
from time import sleep
from typing import Any

from sentinel.process import ProcessHost
from sentinel.supervisor.exceptions import (
    SupervisorRestartError,
    SupervisorShutdownError,
    SupervisorStartupError,
    SupervisorStateError,
)
from sentinel.supervisor.monitor import SupervisorMonitor
from sentinel.supervisor.policy import RestartPolicy
from sentinel.supervisor.state import SupervisorState


class Supervisor:
    """
    Manage and monitor a Sentinel ProcessHost.

    The Supervisor owns the monitor lifecycle and decides whether an
    unexpected process failure should trigger recovery.
    """

    def __init__(
        self,
        process: ProcessHost,
        *,
        policy: RestartPolicy | None = None,
        monitor_interval: float = 1.0,
    ) -> None:
        if not isinstance(process, ProcessHost):
            raise TypeError(
                "process must be a ProcessHost instance."
            )

        if policy is not None and not isinstance(
            policy,
            RestartPolicy,
        ):
            raise TypeError(
                "policy must be a RestartPolicy instance."
            )

        self._process = process
        self._policy = (
            policy
            if policy is not None
            else RestartPolicy()
        )

        self._state = SupervisorState.STOPPED
        self._restart_count = 0
        self._intentional_stop = False
        self._last_recovery_error: BaseException | None = None
        self._lock = RLock()

        self._monitor = SupervisorMonitor(
            process,
            interval=monitor_interval,
            on_failure=self._handle_process_failure,
        )

    @property
    def process(self) -> ProcessHost:
        """Return the supervised ProcessHost."""
        return self._process

    @property
    def policy(self) -> RestartPolicy:
        """Return the restart policy."""
        return self._policy

    @property
    def monitor(self) -> SupervisorMonitor:
        """Return the Supervisor monitor."""
        return self._monitor

    @property
    def state(self) -> SupervisorState:
        """Return the current Supervisor state."""
        with self._lock:
            return self._state

    @property
    def running(self) -> bool:
        """Return whether the Supervisor is running."""
        with self._lock:
            return self._state == SupervisorState.RUNNING

    @property
    def restart_count(self) -> int:
        """Return the number of successful restarts."""
        with self._lock:
            return self._restart_count

    @property
    def intentional_stop(self) -> bool:
        """Return whether the current stop was explicitly requested."""
        with self._lock:
            return self._intentional_stop


    def start(self) -> None:
        """Start Sentinel and begin monitoring it."""
        with self._lock:
            if self._state == SupervisorState.RUNNING:
                raise SupervisorStateError(
                    "Supervisor is already running."
                )
            if self._state in {
                SupervisorState.STARTING,
                SupervisorState.STOPPING,
                SupervisorState.RESTARTING,
            }:
                raise SupervisorStateError(
                    "Supervisor is currently transitioning."
                )
            if self._state == SupervisorState.FAILED:
                raise SupervisorStateError(
                    "Supervisor is in a failed state."
                )

            self._state = SupervisorState.STARTING
            self._intentional_stop = False

        try:
            self._process.start()
            self._monitor.start()
        except Exception as exc:
            cleanup_failures: list[Exception] = []

            try:
                self._monitor.stop()
            except Exception as cleanup_exc:
                cleanup_failures.append(cleanup_exc)

            if self._process.running:
                try:
                    self._process.stop()
                except Exception as cleanup_exc:
                    cleanup_failures.append(cleanup_exc)

            with self._lock:
                self._state = (
                    SupervisorState.FAILED
                    if cleanup_failures
                    else SupervisorState.STOPPED
                )

            if cleanup_failures:
                raise SupervisorStartupError(
                    "Supervisor failed to start Sentinel and "
                    "rollback did not complete cleanly."
                ) from ExceptionGroup(
                    "Supervisor startup and rollback failed.",
                    [exc, *cleanup_failures],
                )

            raise SupervisorStartupError(
                "Supervisor failed to start Sentinel."
            ) from exc

        with self._lock:
            self._state = SupervisorState.RUNNING


    def stop(self) -> None:
        """Intentionally stop Sentinel and its monitor."""
        with self._lock:
            if self._state != SupervisorState.RUNNING:
                raise SupervisorStateError(
                    "Supervisor is not running."
                )

            self._state = SupervisorState.STOPPING
            self._intentional_stop = True

        shutdown_failures: list[Exception] = []

        try:
            self._monitor.stop()
        except Exception as exc:
            shutdown_failures.append(exc)

        try:
            self._process.stop()
        except Exception as exc:
            shutdown_failures.append(exc)

        with self._lock:
            self._state = (
                SupervisorState.FAILED
                if shutdown_failures
                else SupervisorState.STOPPED
            )

        if shutdown_failures:
            cause: BaseException
            if len(shutdown_failures) == 1:
                cause = shutdown_failures[0]
            else:
                cause = ExceptionGroup(
                    "Supervisor shutdown failed.",
                    shutdown_failures,
                )

            raise SupervisorShutdownError(
                "Supervisor failed to stop Sentinel."
            ) from cause


    def restart(self) -> None:
        """Explicitly restart Sentinel."""
        with self._lock:
            if self._state != SupervisorState.RUNNING:
                raise SupervisorStateError(
                    "Supervisor is not running."
                )

            self._state = SupervisorState.RESTARTING
            self._intentional_stop = True

        restart_failures: list[Exception] = []

        try:
            self._monitor.stop()
        except Exception as exc:
            restart_failures.append(exc)

        try:
            self._process.stop()
        except Exception as exc:
            restart_failures.append(exc)

        if restart_failures:
            with self._lock:
                self._state = SupervisorState.FAILED

            cause: BaseException
            if len(restart_failures) == 1:
                cause = restart_failures[0]
            else:
                cause = ExceptionGroup(
                    "Supervisor restart shutdown failed.",
                    restart_failures,
                )

            raise SupervisorRestartError(
                "Supervisor failed to stop Sentinel for restart."
            ) from cause

        try:
            self._wait_for_backoff()
            self._process.start()
            self._monitor.start()
        except Exception as exc:
            rollback_failures: list[Exception] = []

            if self._monitor.running:
                try:
                    self._monitor.stop()
                except Exception as rollback_exc:
                    rollback_failures.append(rollback_exc)

            if self._process.running:
                try:
                    self._process.stop()
                except Exception as rollback_exc:
                    rollback_failures.append(rollback_exc)

            with self._lock:
                self._state = SupervisorState.FAILED

            if rollback_failures:
                raise SupervisorRestartError(
                    "Supervisor failed to restart Sentinel and "
                    "rollback did not complete cleanly."
                ) from ExceptionGroup(
                    "Supervisor restart and rollback failed.",
                    [exc, *rollback_failures],
                )

            raise SupervisorRestartError(
                "Supervisor failed to restart Sentinel."
            ) from exc

        with self._lock:
            self._restart_count += 1
            self._intentional_stop = False
            self._state = SupervisorState.RUNNING

    def _wait_for_backoff(self) -> None:
        """Wait for the configured restart backoff period."""
        delay = self._policy.backoff_seconds

        if delay > 0:
            sleep(delay)


    def _handle_process_failure(self) -> None:
        """Handle an unexpected process termination from the monitor thread."""
        with self._lock:
            if self._intentional_stop:
                return

            if self._state != SupervisorState.RUNNING:
                return

            self._state = SupervisorState.RESTARTING

        if not self._policy.enabled:
            with self._lock:
                self._state = SupervisorState.DEGRADED
            return

        with self._lock:
            if self._restart_count >= self._policy.max_restarts:
                self._state = SupervisorState.FAILED
                return

        try:
            self._wait_for_backoff()
            self._process.start()
            self._monitor.start()
        except Exception as exc:
            rollback_failures: list[Exception] = []

            if self._monitor.running:
                try:
                    self._monitor.stop()
                except Exception as rollback_exc:
                    rollback_failures.append(rollback_exc)

            if self._process.running:
                try:
                    self._process.stop()
                except Exception as rollback_exc:
                    rollback_failures.append(rollback_exc)

            with self._lock:
                self._state = SupervisorState.FAILED
                if rollback_failures:
                    self._last_recovery_error = ExceptionGroup(
                        "Supervisor automatic recovery failed.",
                        [exc, *rollback_failures],
                    )
                else:
                    self._last_recovery_error = exc
            return

        with self._lock:
            self._restart_count += 1
            self._state = SupervisorState.RUNNING


    def health(self) -> dict[str, Any]:
        """Return Supervisor, monitor, and process health."""
        with self._lock:
            state = self._state
            restart_count = self._restart_count
            intentional_stop = self._intentional_stop
            recovery_error = self._last_recovery_error

        process_health = self._process.health()

        recovery_error_details: dict[str, Any] | None = None
        if recovery_error is not None:
            if isinstance(recovery_error, ExceptionGroup):
                recovery_error_details = {
                    "type": type(recovery_error).__name__,
                    "message": str(recovery_error),
                    "errors": [
                        {
                            "type": type(error).__name__,
                            "message": str(error),
                        }
                        for error in recovery_error.exceptions
                    ],
                }
            else:
                recovery_error_details = {
                    "type": type(recovery_error).__name__,
                    "message": str(recovery_error),
                }

        return {
            "state": state.value,
            "running": state == SupervisorState.RUNNING,
            "healthy": (
                state == SupervisorState.RUNNING
                and process_health.get("healthy") is True
            ),
            "restart_count": restart_count,
            "intentional_stop": intentional_stop,
            "last_recovery_error": recovery_error_details,
            "monitor": {
                "running": self._monitor.running,
                "failure_detected": self._monitor.failure_detected,
                "interval": self._monitor.interval,
            },
            "policy": {
                "enabled": self._policy.enabled,
                "max_restarts": self._policy.max_restarts,
                "backoff_seconds": self._policy.backoff_seconds,
            },
            "process": process_health,
        }

    def __repr__(self) -> str:
        return (
            "Supervisor("
            f"state={self.state.value!r}, "
            f"running={self.running}, "
            f"restart_count={self.restart_count}"
            ")"
        )