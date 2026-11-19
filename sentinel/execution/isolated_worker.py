"""Parent-side supervisor for isolated callable workers."""

from __future__ import annotations

import json
import os
import shutil
import signal
import subprocess
import sys
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

from sentinel.execution.exceptions import (
    ExecutionTimeoutError,
    ProcessError,
)


@dataclass(frozen=True, slots=True)
class WorkerLimits:
    """Best-effort OS resource limits for one worker process."""

    cpu_seconds: int = 30
    memory_bytes: int = 512 * 1024 * 1024
    file_size_bytes: int = 64 * 1024 * 1024
    open_files: int = 64
    max_output_chars: int = 16_384
    max_result_bytes: int = 1_048_576

    def __post_init__(self) -> None:
        for name in (
            "cpu_seconds", "memory_bytes", "file_size_bytes",
            "open_files", "max_output_chars", "max_result_bytes",
        ):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int):
                raise TypeError(f"{name} must be an integer.")
            if value <= 0:
                raise ValueError(f"{name} must be greater than zero.")


class IsolatedWorker:
    """Run explicitly allowlisted importable callables in disposable processes.

    This is a process boundary with OS resource controls, not a complete
    security sandbox. On POSIX, rlimits are applied in the child. On Windows,
    a Job Object is assigned before the callable request is sent to the worker.
    Filesystem and network access still require an external OS/container policy.
    """

    def __init__(
        self,
        *,
        allowed_modules: set[str],
        limits: WorkerLimits | None = None,
        cwd: str | Path | None = None,
        terminate_grace_seconds: float = 1.0,
        bubblewrap: bool = False,
    ) -> None:
        if not allowed_modules or any(
            not isinstance(name, str) or not name.strip()
            for name in allowed_modules
        ):
            raise ValueError("allowed_modules must contain module names.")
        if terminate_grace_seconds <= 0:
            raise ValueError("terminate_grace_seconds must be positive.")
        self._allowed_modules = frozenset(allowed_modules)
        self._limits = limits or WorkerLimits()
        self._cwd = Path(cwd).resolve() if cwd is not None else None
        self._grace = terminate_grace_seconds
        self._bubblewrap = bubblewrap
        if bubblewrap:
            if sys.platform != "linux":
                raise RuntimeError("bubblewrap isolation is supported only on Linux")
            if self._cwd is None or not self._cwd.is_dir():
                raise ValueError("bubblewrap requires an existing dedicated worker cwd")
            if shutil.which("bwrap") is None:
                raise RuntimeError("bubblewrap (bwrap) is required for OS sandboxing")

    @property
    def limits(self) -> WorkerLimits:
        return self._limits

    def execute(
        self,
        callable_ref: str,
        *args: Any,
        timeout: float = 30.0,
        **kwargs: Any,
    ) -> Any:
        """Execute an allowlisted ``module:callable`` reference."""
        self._validate_reference(callable_ref)
        if timeout <= 0:
            raise ValueError("timeout must be greater than zero.")

        request = {
            "callable": callable_ref,
            "args": list(args),
            "kwargs": kwargs,
            "max_output_chars": self._limits.max_output_chars,
            "max_result_bytes": self._limits.max_result_bytes,
        }
        try:
            payload = json.dumps(request, ensure_ascii=False, allow_nan=False)
        except (TypeError, ValueError) as exc:
            raise ProcessError("Worker arguments must be JSON-serializable.") from exc

        process = self._start_worker()
        job = None
        try:
            if os.name == "nt":
                job = _WindowsJob(process.pid, self._limits)
            else:
                self._apply_posix_limits(process.pid)

            try:
                stdout, _ = process.communicate(
                    payload,
                    timeout=min(timeout, float(self._limits.cpu_seconds) + 1.0),
                )
            except subprocess.TimeoutExpired as exc:
                self._terminate(process, job)
                raise ExecutionTimeoutError(
                    f"Isolated worker exceeded its {timeout:g}s deadline."
                ) from exc

            if (
                len(stdout.encode("utf-8", errors="replace"))
                > self._limits.max_result_bytes
            ):
                raise ProcessError(
                    "Worker response exceeded the configured size limit."
                )
            try:
                response = json.loads(stdout)
            except json.JSONDecodeError as exc:
                raise ProcessError(
                    "Worker returned an invalid protocol response."
                ) from exc
            if (
                not isinstance(response, dict)
                or not isinstance(response.get("ok"), bool)
            ):
                raise ProcessError("Worker returned an invalid protocol response.")
            if not response["ok"]:
                error_type = response.get("error_type", "WorkerError")
                error = response.get("error", "Worker execution failed.")
                raise ProcessError(f"{error_type}: {error}")
            return response.get("result")
        finally:
            if process.poll() is None:
                self._terminate(process, job)
            if job is not None:
                job.close()

    def _validate_reference(self, callable_ref: str) -> str:
        if not isinstance(callable_ref, str) or ":" not in callable_ref:
            raise ValueError("callable_ref must use 'module:qualified_name'.")
        module_name, qualified_name = callable_ref.split(":", 1)
        if not qualified_name or "<locals>" in qualified_name:
            raise ValueError(
                "Worker callable must be an importable module-level function."
            )
        if not any(
            module_name == allowed or module_name.startswith(allowed + ".")
            for allowed in self._allowed_modules
        ):
            raise PermissionError(
                f"Worker module '{module_name}' is not in the configured allowlist."
            )
        return module_name

    def _start_worker(self) -> subprocess.Popen[str]:
        env = os.environ.copy()
        if os.name == "posix":
            env.update({
                "SENTINEL_WORKER_CPU_SECONDS": str(self._limits.cpu_seconds),
                "SENTINEL_WORKER_MEMORY_BYTES": str(self._limits.memory_bytes),
                "SENTINEL_WORKER_FILE_SIZE_BYTES": str(self._limits.file_size_bytes),
                "SENTINEL_WORKER_OPEN_FILES": str(self._limits.open_files),
            })
        try:
            command = [sys.executable, "-m", "sentinel.execution.worker"]
            if self._bubblewrap:
                assert self._cwd is not None
                command = [
                    shutil.which("bwrap") or "bwrap",
                    "--die-with-parent", "--new-session", "--unshare-net",
                    "--ro-bind", "/", "/", "--dev", "/dev", "--proc", "/proc",
                    # Private tmpfs mount inside Bubblewrap's isolated namespace.
                    "--tmpfs", "/tmp",  # nosec B108
                    "--bind", str(self._cwd), str(self._cwd),
                    "--chdir", str(self._cwd), "--", *command,
                ]
            return subprocess.Popen(
                command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True,
                encoding="utf-8",
                errors="replace",
                cwd=self._cwd,
                env=env,
                shell=False,
                start_new_session=(os.name == "posix"),
                creationflags=(
                    cast(int, getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0))
                    if os.name == "nt"
                    else 0
                ),
            )
        except OSError as exc:
            raise ProcessError(f"Could not start isolated worker: {exc}") from exc

    def _apply_posix_limits(self, pid: int) -> None:
        # The worker applies rlimits before reading the request or importing
        # any user module. This method remains as a platform-specific hook.
        del pid

    def _terminate(self, process: subprocess.Popen[str], job: Any) -> None:
        # Kill the containment group even if the worker leader has already
        # exited: a descendant may still hold inherited protocol pipe handles.
        if job is not None:
            job.terminate()
        elif os.name == "posix":
            try:
                getattr(os, "killpg")(process.pid, signal.SIGTERM)  # noqa: B009
            except ProcessLookupError:
                pass
            if process.poll() is None:
                try:
                    process.wait(timeout=self._grace)
                except subprocess.TimeoutExpired:
                    pass
            try:
                getattr(os, "killpg")(process.pid, getattr(signal, "SIGKILL"))  # noqa: B009
            except ProcessLookupError:
                pass
        elif process.poll() is None:
            process.terminate()

        if process.poll() is None:
            try:
                process.wait(timeout=self._grace)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()


class _WindowsJob:
    """Windows Job Object with kill-on-close, memory and CPU time limits."""

    def __init__(self, pid: int, limits: WorkerLimits) -> None:
        import ctypes
        from ctypes import wintypes

        self._ctypes = ctypes
        ctypes_api = cast(Any, ctypes)
        get_last_error = cast(Callable[[], int], ctypes_api.get_last_error)
        win_dll = cast(Callable[..., Any], ctypes_api.WinDLL)
        self._kernel32 = win_dll("kernel32", use_last_error=True)
        self._kernel32.CreateJobObjectW.restype = wintypes.HANDLE
        self._kernel32.CreateJobObjectW.argtypes = [ctypes.c_void_p, wintypes.LPCWSTR]
        self._kernel32.OpenProcess.restype = wintypes.HANDLE
        self._kernel32.OpenProcess.argtypes = [
            wintypes.DWORD,
            wintypes.BOOL,
            wintypes.DWORD,
        ]
        self._kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
        self._kernel32.CloseHandle.restype = wintypes.BOOL
        self._kernel32.SetInformationJobObject.argtypes = [
            wintypes.HANDLE, wintypes.INT, ctypes.c_void_p, wintypes.DWORD,
        ]
        self._kernel32.SetInformationJobObject.restype = wintypes.BOOL
        self._kernel32.AssignProcessToJobObject.argtypes = [
            wintypes.HANDLE, wintypes.HANDLE,
        ]
        self._kernel32.AssignProcessToJobObject.restype = wintypes.BOOL
        self._kernel32.TerminateJobObject.argtypes = [
            wintypes.HANDLE, wintypes.UINT,
        ]
        self._kernel32.TerminateJobObject.restype = wintypes.BOOL
        self._handle = self._kernel32.CreateJobObjectW(None, None)
        if not self._handle:
            raise OSError(get_last_error(), "CreateJobObjectW failed")

        class BasicLimit(ctypes.Structure):
            _fields_ = [
                ("PerProcessUserTimeLimit", ctypes.c_longlong),
                ("PerJobUserTimeLimit", ctypes.c_longlong),
                ("LimitFlags", wintypes.DWORD),
                ("MinimumWorkingSetSize", ctypes.c_size_t),
                ("MaximumWorkingSetSize", ctypes.c_size_t),
                ("ActiveProcessLimit", wintypes.DWORD),
                ("Affinity", ctypes.c_size_t),
                ("PriorityClass", wintypes.DWORD),
                ("SchedulingClass", wintypes.DWORD),
            ]

        class IoCounters(ctypes.Structure):
            _fields_ = [(name, ctypes.c_ulonglong) for name in (
                "ReadOperationCount", "WriteOperationCount", "OtherOperationCount",
                "ReadTransferCount", "WriteTransferCount", "OtherTransferCount",
            )]

        class ExtendedLimit(ctypes.Structure):
            _fields_ = [
                ("BasicLimitInformation", BasicLimit),
                ("IoInfo", IoCounters),
                ("ProcessMemoryLimit", ctypes.c_size_t),
                ("JobMemoryLimit", ctypes.c_size_t),
                ("PeakProcessMemoryUsed", ctypes.c_size_t),
                ("PeakJobMemoryUsed", ctypes.c_size_t),
            ]

        info = ExtendedLimit()
        info.BasicLimitInformation.LimitFlags = (
            0x00002000  # JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
            | 0x00000100  # JOB_OBJECT_LIMIT_PROCESS_MEMORY
            | 0x00000002  # JOB_OBJECT_LIMIT_PROCESS_TIME
        )
        info.BasicLimitInformation.PerProcessUserTimeLimit = (
            limits.cpu_seconds * 10_000_000
        )
        info.BasicLimitInformation.ActiveProcessLimit = 16
        info.ProcessMemoryLimit = limits.memory_bytes
        if not self._kernel32.SetInformationJobObject(
            self._handle, 9, ctypes.byref(info), ctypes.sizeof(info)
        ):
            self.close()
            raise OSError(get_last_error(), "SetInformationJobObject failed")

        access = 0x0100 | 0x0001  # PROCESS_SET_QUOTA | PROCESS_TERMINATE
        process_handle = self._kernel32.OpenProcess(access, False, pid)
        if not process_handle:
            self.close()
            raise OSError(get_last_error(), "OpenProcess failed")
        try:
            if not self._kernel32.AssignProcessToJobObject(
                self._handle,
                process_handle,
            ):
                error_code = get_last_error()
                self.close()
                raise OSError(
                    error_code,
                    "AssignProcessToJobObject failed",
                )
        finally:
            self._kernel32.CloseHandle(process_handle)

    def terminate(self) -> None:
        if self._handle:
            self._kernel32.TerminateJobObject(self._handle, 1)

    def close(self) -> None:
        if self._handle:
            self._kernel32.CloseHandle(self._handle)
            self._handle = None
