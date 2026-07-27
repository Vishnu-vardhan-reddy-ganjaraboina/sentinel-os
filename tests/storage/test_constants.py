from sentinel.storage.constants import (
    DEFAULT_CACHE_SIZE,
    DEFAULT_ENGINE_NAME,
    DEFAULT_MEMORY_NAMESPACE,
    DEFAULT_SERIALIZATION_FORMAT,
    DEFAULT_STORAGE_BACKEND,
    DEFAULT_STORAGE_DIRECTORY,
)


def test_default_backend():
    assert DEFAULT_STORAGE_BACKEND == "memory"


def test_serialization():
     assert DEFAULT_SERIALIZATION_FORMAT == "json"


def test_cache():
    assert DEFAULT_CACHE_SIZE > 0


def test_directory():
    assert DEFAULT_STORAGE_DIRECTORY == "storage"


def test_engine():
    assert DEFAULT_ENGINE_NAME == "SentinelStorage"


def test_namespace():
    assert DEFAULT_MEMORY_NAMESPACE == "default"