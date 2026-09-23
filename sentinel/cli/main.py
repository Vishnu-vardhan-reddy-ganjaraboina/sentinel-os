"""
Sentinel OS command-line interface.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Sequence

from sentinel.boot import (
    BootConfiguration,
    BootManager,
    BootProfile,
)
from sentinel.cli.kernel_control import CLIKernelControl
from sentinel.control import (
    ControlClient,
    ControlEndpointRegistry,
)
from sentinel.control_plane.commands import KernelCommand
from sentinel.control_plane.endpoint_registry import (
    ControlPlaneEndpointRegistry,
)
from sentinel.control_plane.result import ControlResult
from sentinel.process import ProcessHost


DEFAULT_CONFIG = Path("configs/development.yaml")


class CLI:
    """Command-line interface for Sentinel OS."""

    def __init__(
        self,
        *,
        endpoint_registry: ControlEndpointRegistry | None = None,
        kernel_endpoint_registry: (
            ControlPlaneEndpointRegistry | None
        ) = None,
    ) -> None:
        if endpoint_registry is not None and not isinstance(
            endpoint_registry,
            ControlEndpointRegistry,
        ):
            raise TypeError(
                "endpoint_registry must be a "
                "ControlEndpointRegistry instance."
            )

        if kernel_endpoint_registry is not None and not isinstance(
            kernel_endpoint_registry,
            ControlPlaneEndpointRegistry,
        ):
            raise TypeError(
                "kernel_endpoint_registry must be a "
                "ControlPlaneEndpointRegistry instance."
            )

        self._process: ProcessHost | None = None

        self._endpoint_registry = (
            endpoint_registry
            if endpoint_registry is not None
            else ControlEndpointRegistry()
        )

        self._kernel_control = CLIKernelControl(
            endpoint_registry=kernel_endpoint_registry,
        )

    @property
    def process(self) -> ProcessHost | None:
        """Return the current process host, if initialized."""
        return self._process

    @property
    def boot(self) -> BootManager | None:
        """Return the current BootManager, if initialized."""
        if self._process is None:
            return None

        return self._process.boot_manager

    @property
    def endpoint_registry(self) -> ControlEndpointRegistry:
        """Return the process control endpoint registry."""
        return self._endpoint_registry

    @property
    def kernel_control(self) -> CLIKernelControl:
        """Return the Kernel Control Plane CLI adapter."""
        return self._kernel_control

    def run(
        self,
        argv: Sequence[str] | None = None,
    ) -> int:
        """Parse arguments and execute the requested command."""
        parser = self._build_parser()
        args = parser.parse_args(argv)

        if args.command == "start":
            return self._start(
                config_path=args.config,
                profile_name=args.profile,
            )

        if args.command == "stop":
            return self._stop()

        if args.command == "status":
            return self._status()

        if args.command == "health":
            return self._health()

        if args.command == "system":
            return self._kernel_system_command(
                args.system_command,
            )

        if args.command == "service":
            return self._kernel_service_command(
                args.service_command,
                getattr(args, "name", None),
            )

        parser.error(
            f"Unknown command: {args.command}"
        )
        return 2

    @staticmethod
    def _build_parser() -> argparse.ArgumentParser:
        """Create the CLI argument parser."""
        parser = argparse.ArgumentParser(
            prog="sentinel",
            description="Sentinel Operating System",
        )

        subparsers = parser.add_subparsers(
            dest="command",
            required=True,
        )

        # ------------------------------------------------------------------
        # Process-level commands
        # ------------------------------------------------------------------

        start_parser = subparsers.add_parser(
            "start",
            help="Start Sentinel OS.",
        )

        start_parser.add_argument(
            "--config",
            type=Path,
            default=DEFAULT_CONFIG,
            help=(
                "Path to the Sentinel YAML configuration "
                f"(default: {DEFAULT_CONFIG})."
            ),
        )

        start_parser.add_argument(
            "--profile",
            default="default",
            help="Boot profile name.",
        )

        subparsers.add_parser(
            "stop",
            help="Stop Sentinel OS.",
        )

        subparsers.add_parser(
            "status",
            help="Show Sentinel OS process status.",
        )

        subparsers.add_parser(
            "health",
            help="Show Sentinel OS process health.",
        )

        # ------------------------------------------------------------------
        # Kernel Control Plane commands
        # ------------------------------------------------------------------

        system_parser = subparsers.add_parser(
            "system",
            help="Inspect and control the Sentinel Kernel.",
        )

        system_subparsers = system_parser.add_subparsers(
            dest="system_command",
            required=True,
        )

        system_subparsers.add_parser(
            "status",
            help="Show Kernel system status.",
        )

        system_subparsers.add_parser(
            "health",
            help="Show Kernel system health.",
        )

        service_parser = subparsers.add_parser(
            "service",
            help="Inspect and control Kernel services.",
        )

        service_subparsers = service_parser.add_subparsers(
            dest="service_command",
            required=True,
        )

        service_subparsers.add_parser(
            "list",
            help="List Kernel services.",
        )

        service_status_parser = service_subparsers.add_parser(
            "status",
            help="Show Kernel service status.",
        )

        service_status_parser.add_argument(
            "name",
            help="Kernel service name.",
        )

        service_start_parser = service_subparsers.add_parser(
            "start",
            help="Start a Kernel service.",
        )

        service_start_parser.add_argument(
            "name",
            help="Kernel service name.",
        )

        service_stop_parser = service_subparsers.add_parser(
            "stop",
            help="Stop a Kernel service.",
        )

        service_stop_parser.add_argument(
            "name",
            help="Kernel service name.",
        )


        # Replace the hidden compatibility parser with the real nested
        # restart command below.
        service_restart_parser = service_subparsers.add_parser(
            "restart",
            help="Restart a Kernel service.",
        )

        service_restart_parser.add_argument(
            "name",
            help="Kernel service name.",
        )

        return parser

    # ------------------------------------------------------------------
    # Process lifecycle
    # ------------------------------------------------------------------

    def _start(
        self,
        config_path: Path,
        profile_name: str,
    ) -> int:
        """Start Sentinel OS and keep the process alive."""
        if self._process is not None and self._process.running:
            print("Sentinel OS is already running.")
            return 1

        if self._remote_is_running():
            print("Sentinel OS is already running.")
            return 1

        configuration = BootConfiguration()
        configuration.load(config_path)

        profile = BootProfile(
            name=profile_name,
        )

        boot_manager = BootManager.from_configuration(
            configuration,
            profile,
        )

        process = ProcessHost(
            boot_manager,
            endpoint_registry=self._endpoint_registry,
        )

        self._process = process

        try:
            result = process.start()

            print(result.message)

            try:
                process.wait()
            except KeyboardInterrupt:
                print("Shutdown requested.")

                if process.running:
                    try:
                        process.stop()
                    except Exception as exc:
                        print(
                            f"Sentinel OS shutdown failed: {exc}"
                        )
                        return 1

                return 0

            if process.running:
                process.stop()

            return 0

        except KeyboardInterrupt:
            print("Shutdown requested.")

            if process.running:
                try:
                    process.stop()
                except Exception as exc:
                    print(
                        f"Sentinel OS shutdown failed: {exc}"
                    )
                    return 1

            return 0

        except Exception as exc:
            print(
                f"Sentinel OS start failed: {exc}"
            )
            return 1

    def _stop(self) -> int:
        """Stop the running Sentinel process."""
        if self._process is not None and self._process.running:
            try:
                result = self._process.stop()
            except Exception as exc:
                print(
                    f"Sentinel OS shutdown failed: {exc}"
                )
                return 1

            print(result.message)
            return 0

        client = self._remote_client()

        if client is None:
            print("Sentinel OS is not running.")
            return 1

        try:
            success, _data, error = client.stop()
        except Exception as exc:
            print(
                f"Unable to contact Sentinel OS: {exc}"
            )
            return 1

        if not success:
            print(
                error
                if error is not None
                else "Sentinel OS shutdown failed."
            )
            return 1

        print(
            "Sentinel OS shutdown requested."
        )
        return 0

    def _status(self) -> int:
        """Show current Sentinel OS process status."""
        if self._process is not None:
            print(
                "Sentinel OS: "
                f"{self._process.state.value}"
            )
            return 0

        client = self._remote_client()

        if client is None:
            print("Sentinel OS: stopped")
            return 0

        try:
            success, data, error = client.status()
        except Exception:
            self._endpoint_registry.clear_if_stale()
            print("Sentinel OS: stopped")
            return 0

        if not success:
            print(
                error
                if error is not None
                else "Sentinel OS: unavailable"
            )
            return 1

        state = data.get("state")

        if not isinstance(state, str):
            print("Sentinel OS: unavailable")
            return 1

        print(
            f"Sentinel OS: {state}"
        )
        return 0

    def _health(self) -> int:
        """Show current Sentinel OS process health."""
        if self._process is not None:
            health = self._process.health()

            print(
                f"Sentinel OS: {health['state']}\n"
                f"Healthy: {str(health['healthy']).lower()}"
            )

            return 0 if health["healthy"] else 1

        client = self._remote_client()

        if client is None:
            print(
                "Sentinel OS: stopped\n"
                "Healthy: false"
            )
            return 1

        try:
            success, data, error = client.health()
        except Exception:
            self._endpoint_registry.clear_if_stale()

            print(
                "Sentinel OS: stopped\n"
                "Healthy: false"
            )
            return 1

        if not success:
            print(
                error
                if error is not None
                else "Sentinel OS health unavailable."
            )
            return 1

        state = data.get("state")
        healthy = data.get("healthy")

        if not isinstance(state, str) or not isinstance(
            healthy,
            bool,
        ):
            print(
                "Sentinel OS health response is invalid."
            )
            return 1

        print(
            f"Sentinel OS: {state}\n"
            f"Healthy: {str(healthy).lower()}"
        )

        return 0 if healthy else 1

    # ------------------------------------------------------------------
    # Kernel Control Plane
    # ------------------------------------------------------------------

    def _kernel_system_command(
        self,
        command: str,
    ) -> int:
        """Execute a Kernel system-level Control Plane command."""
        command_map = {
            "status": KernelCommand.SYSTEM_STATUS,
            "health": KernelCommand.SYSTEM_HEALTH,
        }

        kernel_command = command_map[command]

        try:
            result = self._kernel_control.execute(
                kernel_command,
            )
        except Exception as exc:
            print(
                f"Unable to contact Kernel Control Plane: {exc}"
            )
            return 1

        return self._print_control_result(result)

    def _kernel_service_command(
        self,
        command: str,
        name: str | None,
    ) -> int:
        """Execute a Kernel service Control Plane command."""
        command_map = {
            "list": KernelCommand.SERVICE_LIST,
            "status": KernelCommand.SERVICE_STATUS,
            "start": KernelCommand.SERVICE_START,
            "stop": KernelCommand.SERVICE_STOP,
            "restart": KernelCommand.SERVICE_RESTART,
        }

        kernel_command = command_map[command]

        data: dict[str, Any] = {}

        if command != "list":
            if name is None:
                print("Service name is required.")
                return 2

            data["name"] = name

        try:
            result = self._kernel_control.execute(
                kernel_command,
                data,
            )
        except Exception as exc:
            print(
                f"Unable to contact Kernel Control Plane: {exc}"
            )
            return 1

        return self._print_control_result(result)

    @staticmethod
    def _print_control_result(
        result: ControlResult,
    ) -> int:
        """Print a Kernel Control Plane result."""
        if not result.success:
            print(
                result.error
                if result.error is not None
                else "Kernel Control Plane command failed."
            )
            return 1

        if not result.data:
            print(
                "Command completed successfully."
            )
            return 0

        for key, value in result.data.items():
            print(
                f"{key}: {value}"
            )

        return 0

    # ------------------------------------------------------------------
    # Process Control helpers
    # ------------------------------------------------------------------

    def _remote_client(self) -> ControlClient | None:
        """Create a client for the registered Sentinel process endpoint."""
        try:
            endpoint = self._endpoint_registry.load()
        except (FileNotFoundError, ValueError):
            return None

        return ControlClient(
            host=endpoint.host,
            port=endpoint.port,
        )

    def _remote_is_running(self) -> bool:
        """Determine whether another Sentinel instance is running."""
        client = self._remote_client()

        if client is None:
            return False

        try:
            success, data, _error = client.status()
        except Exception:
            self._endpoint_registry.clear_if_stale()
            return False

        return (
            success is True
            and data.get("running") is True
        )


def main(
    argv: Sequence[str] | None = None,
) -> int:
    """Run the Sentinel CLI."""
    return CLI().run(argv)