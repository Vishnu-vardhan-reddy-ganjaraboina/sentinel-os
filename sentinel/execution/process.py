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
    """Manages long-running operating system processes."""

    def __init__(
        self,
        *,
        shell: bool = DEFAULT_SHELL,
        cwd: str | Path | None = None,
    ) -> None:
        if shell:
            raise ValueError(
                "shell=True is not supported; pass an argument sequence"
            )

        self._shell = False
        self._cwd = Path(cwd).resolve() if cwd else None
        self._process: subprocess.Popen[str] | None = None
        self._lock = RLock()
        self._shutdown = False

    @property
    def process(self) -> subprocess.Popen[str] | None:
        with self._lock:
            return self._process

    @property
    def pid(self) -> int | None:
        with self._lock:
            return None if self._process is None else self._process.pid

    @property
    def is_running(self) -> bool:
        with self._lock:
            return (
                self._process is not None
                and self._process.poll() is None
            )

    def start(self, command: Sequence[str]) -> int:
        """Start a new process."""
        with self._lock:
            if self._shutdown:
                raise ProcessError("Process manager has been shut down.")

            if self._process is not None:
                if self._process.poll() is None:
                    raise ProcessError("A process is already running.")
                self._close_streams(self._process)
                self._process = None

            if not command or any(not isinstance(arg, str) for arg in command):
                raise ProcessError("Command must be a non-empty sequence of strings.")

            try:
                process = subprocess.Popen(
                    list(command),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    stdin=subprocess.PIPE,
                    text=TEXT_MODE,
                    cwd=self._cwd,
                    shell=False,
                )
            except OSError as exc:
                raise ProcessError(str(exc)) from exc

            self._process = process
            return process.pid

    def wait(self, timeout: float | None = None) -> int:
        """Wait for the process to finish and return its exit code."""
        with self._lock:
            process = self._process
            if process is None:
                raise ProcessError("No process has been started.")

        # Do not hold the manager lock while waiting: terminate() must
        # be able to signal a process another thread is waiting for.
        try:
            return process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            raise


    def terminate(self) -> None:
        """Terminate the process, escalating to kill if necessary."""
        with self._lock:
            process = self._process

        if process is None:
            return

        try:
            if process.poll() is None:
                process.terminate()

            try:
                process.wait(timeout=DEFAULT_TERMINATE_TIMEOUT)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
        finally:
            with self._lock:
                if self._process is process:
                    self._close_streams(process)
                    self._process = None

    def read_output(self) -> tuple[str, str]:
        """Collect stdout and stderr from the process."""
        with self._lock:
            process = self._process

        if process is None:
            raise ProcessError("No process has been started.")

        try:
            stdout, stderr = process.communicate()
            return stdout or "", stderr or ""
        finally:
            if process.poll() is not None:
                with self._lock:
                    if self._process is process:
                        self._close_streams(process)
                        self._process = None

    def shutdown(self) -> None:
        """Prevent future starts and clean up any managed process."""
        with self._lock:
            if self._shutdown:
                return
            self._shutdown = True

        self.terminate()

    @staticmethod
    def _close_streams(process: subprocess.Popen[str]) -> None:
        for stream in (process.stdin, process.stdout, process.stderr):
            if stream is not None and not stream.closed:
                stream.close()
