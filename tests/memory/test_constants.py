from sentinel.memory.constants import (
    DEFAULT_IMPORTANCE,
    DEFAULT_MEMORY_VERSION,
    DEFAULT_TTL,
    MemoryStatus,
    MemoryType,
)


def test_default_version():
    assert DEFAULT_MEMORY_VERSION == "1.0.0"


def test_default_importance():
    assert DEFAULT_IMPORTANCE == 1


def test_default_ttl():
    assert DEFAULT_TTL is None


def test_memory_types():
    assert MemoryType.WORKING.value == "working"
    assert MemoryType.SHORT_TERM.value == "short_term"
    assert MemoryType.LONG_TERM.value == "long_term"
    assert MemoryType.EPISODIC.value == "episodic"
    assert MemoryType.SEMANTIC.value == "semantic"


def test_memory_status():
    assert MemoryStatus.ACTIVE.value == "active"
    assert MemoryStatus.ARCHIVED.value == "archived"
    assert MemoryStatus.EXPIRED.value == "expired"
    assert MemoryStatus.DELETED.value == "deleted"