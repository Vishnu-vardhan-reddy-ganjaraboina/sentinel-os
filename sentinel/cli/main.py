"""
Sentinel OS command-line interface.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

from sentinel.boot import (
    BootConfiguration,
    BootManager,
    BootProfile,
)
from sentinel.control import (
    ControlClient,
    ControlEndpointRegistry,
)
from sentinel.process import ProcessHost


DEFAULT_CONFIG = Path("configs/development.yaml")


class CLI:
    """Command-line interface for Sentinel OS."""

    def __init__(
        self,
        *,
        endpoint_registry: ControlEndpointRegistry | None = None,
    ) -> None:
        if endpoint_registry is not None and not isinstance(
            endpoint_registry,
            ControlEndpointRegistry,
        ):
            raise TypeError(
                "endpoint_registry must be a "
                "ControlEndpointRegistry instance."
            )

        self._process: ProcessHost | None = None
        self._endpoint_registry = (
            endpoint_registry
            if endpoint_registry is not None
            else ControlEndpointRegistry()
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
        """Return the control endpoint registry."""
        return self._endpoint_registry

    def run(self, argv: Sequence[str] | None = None) -> int:
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

        parser.error(f"Unknown command: {args.command}")
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
            help="Show Sentinel OS status.",
        )

        subparsers.add_parser(
            "health",
            help="Show Sentinel OS health.",
        )

        return parser

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

        profile = BootProfile(name=profile_name)

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

            process.wait()

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
            print(f"Sentinel OS start failed: {exc}")
            return 1

    def _stop(self) -> int:
        """Stop the running Sentinel process."""
        if self._process is not None and self._process.running:
            try:
                result = self._process.stop()
            except Exception as exc:
                print(f"Sentinel OS shutdown failed: {exc}")
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
            print(f"Unable to contact Sentinel OS: {exc}")
            return 1

        if not success:
            print(
                error
                if error is not None
                else "Sentinel OS shutdown failed."
            )
            return 1

        print("Sentinel OS shutdown requested.")
        return 0

    def _status(self) -> int:
        """Show current Sentinel OS status."""
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

        print(f"Sentinel OS: {state}")
        return 0

    def _health(self) -> int:
        """Show current Sentinel OS health."""
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

    def _remote_client(self) -> ControlClient | None:
        """Create a client for the registered Sentinel endpoint."""
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
