import pytest

from sentinel.memory.interfaces import Memory, MemoryEntry


class DummyEntry(MemoryEntry):

    @property
    def id(self):
        return "memory.1"

    @property
    def content(self):
        return {"text": "Hello Sentinel"}

    @property
    def importance(self):
        return 5

    @property
    def expired(self):
        return False


class DummyMemory(Memory):

    def __init__(self):
        self._entries = {}

    def add(self, entry):
        self._entries[entry.id] = entry

    def get(self, memory_id):
        return self._entries[memory_id]

    def remove(self, memory_id):
        del self._entries[memory_id]

    def exists(self, memory_id):
        return memory_id in self._entries

    def search(self, keyword):
        return [
            entry
            for entry in self._entries.values()
            if keyword.lower() in str(entry.content).lower()
        ]

    def clear(self):
        self._entries.clear()


def test_entry_properties():
    entry = DummyEntry()

    assert entry.id == "memory.1"
    assert entry.content["text"] == "Hello Sentinel"
    assert entry.importance == 5
    assert entry.expired is False


def test_memory_add_get():
    memory = DummyMemory()
    entry = DummyEntry()

    memory.add(entry)

    assert memory.get("memory.1") is entry


def test_memory_exists():
    memory = DummyMemory()
    entry = DummyEntry()

    memory.add(entry)

    assert memory.exists("memory.1")


def test_memory_remove():
    memory = DummyMemory()
    entry = DummyEntry()

    memory.add(entry)
    memory.remove("memory.1")

    assert not memory.exists("memory.1")


def test_memory_search():
    memory = DummyMemory()
    entry = DummyEntry()

    memory.add(entry)

    results = memory.search("Sentinel")

    assert len(results) == 1
    assert results[0] is entry


def test_memory_clear():
    memory = DummyMemory()

    memory.add(DummyEntry())
    memory.clear()

    assert not memory.exists("memory.1")


def test_memory_entry_is_abstract():
    with pytest.raises(TypeError):
        MemoryEntry()


def test_memory_is_abstract():
    with pytest.raises(TypeError):
        Memory()