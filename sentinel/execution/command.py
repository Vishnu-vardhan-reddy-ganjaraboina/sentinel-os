"""
Command execution utilities for the Execution subsystem.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from sentinel.execution.constants import (
    CAPTURE_OUTPUT,
    DEFAULT_SHELL,
    DEFAULT_TIMEOUT_SECONDS,
    TEXT_MODE,
)
from sentinel.execution.exceptions import (
    CommandError,
    ExecutionTimeoutError,
)


@dataclass(slots=True, frozen=True)
class CommandResult:
    """
    Represents the result of a command execution.
    """

    command: tuple[str, ...]
    returncode: int
    stdout: str
    stderr: str

    @property
    def succeeded(self) -> bool:
        return self.returncode == 0


class CommandExecutor:
    """
    Executes operating system commands safely.
    """

    def __init__(
        self,
        *,
        shell: bool = DEFAULT_SHELL,
        timeout: int = DEFAULT_TIMEOUT_SECONDS,
        cwd: str | Path | None = None,
    ) -> None:
        self._shell = shell
        self._timeout = timeout
        self._cwd = Path(cwd).resolve() if cwd else None

    def run(
        self,
        command: Sequence[str],
    ) -> CommandResult:
        """
        Execute a command and return its result.
        """
        if not command:
            raise ValueError("command cannot be empty.")

        try:
            completed = subprocess.run(
                list(command),
                capture_output=CAPTURE_OUTPUT,
                text=TEXT_MODE,
                timeout=self._timeout,
                shell=self._shell,
                cwd=self._cwd,
                check=False,
            )

        except subprocess.TimeoutExpired as exc:
            raise ExecutionTimeoutError(
                f"Command timed out after {self._timeout} seconds."
            ) from exc

        except OSError as exc:
            raise CommandError(str(exc)) from exc

        return CommandResult(
            command=tuple(command),
            returncode=completed.returncode,
            stdout=completed.stdout,
            stderr=completed.stderr,
        )

    def run_checked(
        self,
        command: Sequence[str],
    ) -> CommandResult:
        """
        Execute a command and raise an exception if it fails.
        """
        result = self.run(command)

        if not result.succeeded:
            raise CommandError(
                f"Command failed with exit code "
                f"{result.returncode}: "
                f"{' '.join(command)}\n"
                f"{result.stderr.strip()}"
            )

        return result