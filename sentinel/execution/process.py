"""
Process management for the Execution subsystem.
"""

from __future__ import annotations

import subprocess
from collections.abc import Sequence
from pathlib import Path
from threading import RLock

from sentinel.execution.constants import (
    DEFAULT_SHELL,
    DEFAULT_TERMINATE_TIMEOUT,
    TEXT_MODE,
)
from sentinel.execution.exceptions import ProcessError


class ProcessManager:
    """
    Manages long-running operating system processes.

    Process ownership and lifecycle state are synchronized so concurrent
    callers cannot start, terminate, or replace the managed process
    inconsistently.
    """

    def __init__(
        self,
        *,
        shell: bool = DEFAULT_SHELL,
        cwd: str | Path | None = None,
    ) -> None:
        self._shell = shell
        self._cwd = Path(cwd).resolve() if cwd else None
        self._process: subprocess.Popen[str] | None = None
        self._lock = RLock()
        self._shutdown = False

    @property
    def process(self) -> subprocess.Popen[str] | None:
        """
        Return the underlying process.

        The returned object is the currently owned process snapshot.
        Callers must not mutate its lifecycle directly.
        """
        with self._lock:
            return self._process

    @property
    def pid(self) -> int | None:
        """Return the process ID."""
        with self._lock:
            process = self._process
            return None if process is None else process.pid

    @property
    def is_running(self) -> bool:
        """Return True if the process is still running."""
        with self._lock:
            process = self._process

        return process is not None and process.poll() is None

    def start(
        self,
        command: Sequence[str],
    ) -> int:
        """
        Start a new process.
        """
        with self._lock:
            if self._shutdown:
                raise ProcessError(
                    "Process manager has been shut down."
                )

            process = self._process

            if process is not None and process.poll() is None:
                raise ProcessError(
                    "A process is already running."
                )

            if process is not None:
                self._close_process_streams(process)
                self._process = None

            try:
                process = subprocess.Popen(
                    list(command),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    stdin=subprocess.PIPE,
                    text=TEXT_MODE,
                    shell=self._shell,
                    cwd=self._cwd,
                )
            except OSError as exc:
                raise ProcessError(str(exc)) from exc

            self._process = process

            return process.pid

    def wait(
        self,
        timeout: float | None = None,
    ) -> int:
        """
        Wait for the process to finish.

        The process remains owned by the manager after ``wait()`` so callers
        can subsequently retrieve stdout/stderr with ``read_output()``.
        """
        with self._lock:
            process = self._require_process()
            return process.wait(timeout)
    def terminate(self) -> None:
        """
        Gracefully terminate the process.

        If graceful termination exceeds the configured timeout, the
        process is killed and reaped.
        """
        with self._lock:
            process = self._process

            if process is None:
                return

            if process.poll() is None:
                process.terminate()

                try:
                    process.wait(DEFAULT_TERMINATE_TIMEOUT)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()

            if self._process is process:
                self._close_process_streams(process)
                self._process = None
    def read_output(self) -> tuple[str, str]:
        """
        Read stdout and stderr and fully reap the process.

        ``communicate()`` drains the communication streams. The process
        reference is cleared after successful completion.
        """
        with self._lock:
            process = self._require_process()

            stdout, stderr = process.communicate()

            if self._process is process:
                self._close_process_streams(process)
                self._process = None

            return stdout, stderr
    def shutdown(self) -> None:
        """
        Terminate any owned process and release its resources.

        Shutdown is idempotent.
        """
        with self._lock:
            if self._shutdown:
                return

            self._shutdown = True

        try:
            self.terminate()
        except Exception:
            with self._lock:
                process = self._process

            if process is not None:
                try:
                    process.kill()
                    process.wait()
                finally:
                    with self._lock:
                        if self._process is process:
                            self._close_process_streams(process)
                            self._process = None

            raise

    def _require_process(self) -> subprocess.Popen[str]:
        process = self._process

        if process is None:
            raise ProcessError("No process has been started.")

        return process

    @staticmethod
    def _close_process_streams(
        process: subprocess.Popen[str],
    ) -> None:
        for stream in (
            process.stdin,
            process.stdout,
            process.stderr,
        ):
            if stream is not None:
                stream.close()
