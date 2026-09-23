from __future__ import annotations

from sentinel.boot.system_factory import SystemFactory
from sentinel.cli import CLI


def test_cli_kernel_control_real_tcp_service_list(
    capsys,
) -> None:
    factory = SystemFactory()
    system = factory.create()

    try:
        system.start()

        registry = system.endpoint_registry
        transport = system.control_transport

        assert registry is not None
        assert transport is not None

        assert system.running is True
        assert transport.running is True
        assert registry.registered is True

        endpoint = registry.load()

        assert endpoint.host == transport.host
        assert endpoint.port == transport.port
        assert endpoint.port > 0

        cli = CLI(
            kernel_endpoint_registry=registry,
        )

        result = cli.run(
            [
                "service",
                "list",
            ]
        )

        captured = capsys.readouterr()

        assert result == 0

        assert "services:" in captured.out
        assert "execution" in captured.out
        assert "memory" in captured.out
        assert "knowledge" in captured.out
        assert "orchestration" in captured.out

    finally:
        system.shutdown()