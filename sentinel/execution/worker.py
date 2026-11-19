"""Child-process entry point for Sentinel isolated callable execution.

This module is intentionally small: it accepts one JSON request on stdin and
writes one JSON response on stdout. User callable output is redirected to
bounded in-memory sinks so it cannot corrupt the protocol.
"""

from __future__ import annotations

import contextlib
import importlib
import io
import json
import os
import sys
from collections.abc import Callable
from typing import Any, cast


class _BoundedSink(io.TextIOBase):
    def __init__(self, limit: int) -> None:
        self.limit = limit
        self.parts: list[str] = []
        self.size = 0
        self.truncated = False

    def write(self, value: str) -> int:
        if not isinstance(value, str):
            value = str(value)
        remaining = self.limit - self.size
        if remaining > 0:
            retained = value[:remaining]
            self.parts.append(retained)
            self.size += len(retained)
        if len(value) > remaining:
            self.truncated = True
        return len(value)

    def flush(self) -> None:
        return None

    def render(self) -> str:
        value = "".join(self.parts)
        if self.truncated:
            value += "\\n[Sentinel: worker output truncated]"
        return value


def _resolve_callable(reference: str) -> Callable[..., Any]:
    module_name, separator, qualified_name = reference.partition(":")
    if not separator or not module_name or not qualified_name:
        raise ValueError("Callable reference must use 'module:qualified_name'.")
    if "<locals>" in qualified_name:
        raise ValueError("Local functions cannot be isolated worker entry points.")
    value: Any = importlib.import_module(module_name)
    for part in qualified_name.split("."):
        value = getattr(value, part)
    if not callable(value):
        raise TypeError("Resolved worker entry point is not callable.")
    return cast(Callable[..., Any], value)


def _apply_resource_limits() -> None:
    if os.name != "posix":
        return
    try:
        resource: Any = importlib.import_module("resource")

        cpu = int(os.environ.get("SENTINEL_WORKER_CPU_SECONDS", "30"))
        memory = int(
            os.environ.get(
                "SENTINEL_WORKER_MEMORY_BYTES",
                str(512 * 1024 * 1024),
            )
        )
        file_size = int(
            os.environ.get(
                "SENTINEL_WORKER_FILE_SIZE_BYTES",
                str(64 * 1024 * 1024),
            )
        )
        open_files = int(os.environ.get("SENTINEL_WORKER_OPEN_FILES", "64"))
        resource.setrlimit(resource.RLIMIT_CPU, (cpu, cpu + 1))
        resource.setrlimit(resource.RLIMIT_AS, (memory, memory))
        resource.setrlimit(resource.RLIMIT_FSIZE, (file_size, file_size))
        resource.setrlimit(resource.RLIMIT_NOFILE, (open_files, open_files))
    except (ImportError, OSError, ValueError) as exc:
        raise RuntimeError("Could not apply required worker resource limits.") from exc


def main() -> int:
    result_limit = 1_048_576
    try:
        _apply_resource_limits()
        request = json.load(sys.stdin)
        if not isinstance(request, dict):
            raise ValueError("Worker request must be a JSON object.")
        reference = request["callable"]
        args = request.get("args", [])
        kwargs = request.get("kwargs", {})
        output_limit = request.get("max_output_chars", 16384)
        result_limit = request.get("max_result_bytes", 1_048_576)
        if not isinstance(reference, str):
            raise TypeError("callable must be a string.")
        if not isinstance(args, list) or not isinstance(kwargs, dict):
            raise TypeError("args must be a list and kwargs must be an object.")
        if isinstance(output_limit, bool) or not isinstance(output_limit, int):
            raise TypeError("max_output_chars must be an integer.")
        if output_limit <= 0:
            raise ValueError("max_output_chars must be positive.")
        if isinstance(result_limit, bool) or not isinstance(result_limit, int):
            raise TypeError("max_result_bytes must be an integer.")
        if result_limit <= 0:
            raise ValueError("max_result_bytes must be positive.")

        stdout_sink = _BoundedSink(output_limit)
        stderr_sink = _BoundedSink(output_limit)
        with (
            contextlib.redirect_stdout(stdout_sink),
            contextlib.redirect_stderr(stderr_sink),
        ):
            target = _resolve_callable(reference)
            result = target(*args, **kwargs)
        response = {
            "ok": True,
            "result": result,
            "stdout": stdout_sink.render(),
            "stderr": stderr_sink.render(),
        }
    except BaseException as exc:
        response = {
            "ok": False,
            "error_type": type(exc).__name__,
            "error": str(exc)[:2048],
        }
    try:
        encoded = json.dumps(response, ensure_ascii=False, allow_nan=False)
    except (TypeError, ValueError):
        encoded = json.dumps({
            "ok": False,
            "error_type": "SerializationError",
            "error": "Worker result is not JSON-serializable.",
        })
    if len(encoded.encode("utf-8")) > result_limit:
        encoded = json.dumps({
            "ok": False,
            "error_type": "ResultLimitError",
            "error": "Worker result exceeded the configured size limit.",
        })
    sys.stdout.write(encoded)
    sys.stdout.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
