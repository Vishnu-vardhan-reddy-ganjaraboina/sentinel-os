from threading import Event, Thread

from sentinel.memory.entry import BaseMemoryEntry
from sentinel.memory.manager import MemoryManager


class CoordinatedEntry(BaseMemoryEntry):
    def __init__(self) -> None:
        super().__init__("memory.race", "test")
        self.expired_checked = Event()
        self.allow_touch = Event()

    @property
    def expired(self) -> bool:
        self.expired_checked.set()
        self.allow_touch.wait(timeout=5)
        return False

    def touch(self) -> None:
        self.allow_touch.set()
        super().touch()


def test_manager_get_can_overlap_remove() -> None:
    entry = CoordinatedEntry()
    manager = MemoryManager()
    manager.store.add(entry)

    result: list[BaseMemoryEntry] = []
    errors: list[Exception] = []

    def read() -> None:
        try:
            result.append(manager.get("memory.race"))
        except Exception as exc:
            errors.append(exc)

    reader = Thread(target=read)
    reader.start()

    try:
        assert entry.expired_checked.wait(timeout=5)
        manager.remove("memory.race")
    finally:
        entry.allow_touch.set()

    reader.join(timeout=5)

    assert not reader.is_alive()
    assert not errors
    assert result == [entry]
    assert not manager.exists("memory.race")
