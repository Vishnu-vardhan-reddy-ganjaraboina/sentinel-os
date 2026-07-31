"""
Process management for the Execution subsystem.
"""

from __future__ import annotations

import subprocess
from collections.abc import Sequence
from pathlib import Path

from sentinel.execution.constants import (
    DEFAULT_SHELL,
    DEFAULT_TERMINATE_TIMEOUT,
    TEXT_MODE,
)
from sentinel.execution.exceptions import ProcessError


class ProcessManager:
    """
    Manages long-running operating system processes.
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

    @property
    def process(self) -> subprocess.Popen[str] | None:
        """
        Return the underlying process.
        """
        return self._process

    @property
    def pid(self) -> int | None:
        """
        Return the process ID.
        """
        return None if self._process is None else self._process.pid

    @property
    def is_running(self) -> bool:
        """
        Return True if the process is still running.
        """
        return (
            self._process is not None
            and self._process.poll() is None
        )

    def start(
        self,
        command: Sequence[str],
    ) -> int:
        """
        Start a new process.
        """
        if self.is_running:
            raise ProcessError(
                "A process is already running."
            )

        try:
            self._process = subprocess.Popen(
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

        return self._process.pid

    def wait(
        self,
        timeout: float | None = None,
    ) -> int:
        """
        Wait for the process to finish.

        Returns
        -------
        int
            Exit code.
        """
        if self._process is None:
            raise ProcessError("No process has been started.")

        return self._process.wait(timeout)

    def terminate(self) -> None:
        """
        Gracefully terminate the process.
        """
        if self._process is None:
            return

        self._process.terminate()

        try:
            self._process.wait(DEFAULT_TERMINATE_TIMEOUT)

        except subprocess.TimeoutExpired:
            self._process.kill()
            self._process.wait()

    def read_output(self) -> tuple[str, str]:
        """
        Read stdout and stderr.
        """
        if self._process is None:
            raise ProcessError("No process has been started.")

        stdout, stderr = self._process.communicate()

        return stdout, stderr