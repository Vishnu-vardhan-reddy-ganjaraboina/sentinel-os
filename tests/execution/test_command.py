import sys

import pytest

from sentinel.execution.command import (
    CommandExecutor,
    CommandResult,
)
from sentinel.execution.exceptions import (
    CommandError,
)


def test_python_version():
    executor = CommandExecutor()

    result = executor.run(
        [sys.executable, "--version"]
    )

    assert isinstance(result, CommandResult)
    assert result.succeeded
    assert "Python" in result.stdout or "Python" in result.stderr


def test_checked_success():
    executor = CommandExecutor()

    result = executor.run_checked(
        [sys.executable, "--version"]
    )

    assert result.succeeded


def test_checked_failure():
    executor = CommandExecutor()

    with pytest.raises(CommandError):
        executor.run_checked(
            [sys.executable, "-c", "import sys; sys.exit(1)"]
        )


def test_empty_command():
    executor = CommandExecutor()

    with pytest.raises(ValueError):
        executor.run([])


def test_command_result_property():
    result = CommandResult(
        command=("echo",),
        returncode=0,
        stdout="ok",
        stderr="",
    )

    assert result.succeeded