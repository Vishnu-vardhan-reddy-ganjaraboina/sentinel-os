from pathlib import Path

import pytest

from sentinel.storage.runtime import StorageRuntimeService


def test_storage_access_before_initialization_raises() -> None:
    service = StorageRuntimeService()

    with pytest.raises(
        RuntimeError,
        match="Storage service is not initialized",
    ):
        _ = service.storage


def test_memory_storage_initializes_and_reports_health() -> None:
    service = StorageRuntimeService(backend="memory")

    assert service.health() == {
        "healthy": False,
        "backend": "memory",
    }

    service.initialize()

    assert service.health() == {
        "healthy": True,
        "backend": "memory",
    }

    service.storage.save("name", "Sentinel")
    assert service.storage.load("name") == "Sentinel"

    service.shutdown()

    assert service.health() == {
        "healthy": False,
        "backend": "memory",
    }


def test_repeated_initialization_preserves_stored_data() -> None:
    service = StorageRuntimeService(backend="memory")

    service.initialize()
    service.storage.save("name", "Sentinel")

    original_manager = service.storage
    service.initialize()

    assert service.storage is original_manager
    assert service.storage.load("name") == "Sentinel"

    service.shutdown()


def test_shutdown_before_initialization_is_safe() -> None:
    service = StorageRuntimeService(backend="memory")

    service.shutdown()
    service.shutdown()

    assert service.health()["healthy"] is False


def test_reinitialization_after_shutdown() -> None:
    service = StorageRuntimeService(backend="memory")

    service.initialize()
    service.storage.save("name", "Sentinel")
    service.shutdown()

    service.initialize()

    assert service.health()["healthy"] is True
    assert not service.storage.exists("name")

    service.shutdown()


def test_sqlite_storage_persists_across_service_restarts(
    tmp_path: Path,
) -> None:
    database = tmp_path / "sentinel.db"

    first = StorageRuntimeService(
        backend="sqlite",
        database=database,
    )
    first.initialize()
    first.storage.save("name", "Sentinel")
    first.shutdown()

    second = StorageRuntimeService(
        backend="sqlite",
        database=database,
    )
    second.initialize()

    assert second.storage.load("name") == "Sentinel"

    second.shutdown()


def test_unsupported_backend_is_rejected() -> None:
    service = StorageRuntimeService(backend="unknown")

    with pytest.raises(
        ValueError,
        match="Unsupported storage backend",
    ):
        service.initialize()

    assert service.health()["healthy"] is False


def test_shutdown_failure_retains_manager_for_cleanup_retry(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from unittest.mock import Mock


    service = StorageRuntimeService(backend="memory")
    service.initialize()

    manager = service.storage
    disconnect = Mock(side_effect=RuntimeError("simulated disconnect failure"))

    monkeypatch.setattr(manager, "disconnect", disconnect)

    with pytest.raises(RuntimeError, match="simulated disconnect failure"):
        service.shutdown()

    # The manager should remain available so cleanup can be retried.
    assert service.storage is manager
    assert service.health()["healthy"] is True

    disconnect.side_effect = None
    service.shutdown()

    disconnect.assert_called_with()
    assert service.health()["healthy"] is False

