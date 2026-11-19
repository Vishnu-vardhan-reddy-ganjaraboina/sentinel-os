from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

from sentinel.memory.entry import BaseMemoryEntry
from sentinel.memory.exceptions import MemoryAlreadyExistsError, MemoryNotFoundError
from sentinel.memory.memory import MemoryStore


def test_concurrent_add_same_id_allows_exactly_one_winner() -> None:
    store = MemoryStore()
    barrier = Barrier(16)

    def add_entry(index: int) -> bool:
        barrier.wait()
        entry = BaseMemoryEntry("shared", index)
        try:
            store.add(entry)
        except MemoryAlreadyExistsError:
            return False
        return True

    with ThreadPoolExecutor(max_workers=16) as pool:
        results = list(pool.map(add_entry, range(16)))

    assert sum(results) == 1
    assert len(store) == 1
    assert store.get("shared").id == "shared"


def test_concurrent_add_remove_preserves_store_integrity() -> None:
    store = MemoryStore()

    for index in range(100):
        store.add(BaseMemoryEntry(f"memory.{index}", index))

    barrier = Barrier(8)

    def remove_entries(worker: int) -> None:
        barrier.wait()
        for index in range(worker, 100, 8):
            try:
                store.remove(f"memory.{index}")
            except MemoryNotFoundError:
                pass

    with ThreadPoolExecutor(max_workers=8) as pool:
        list(pool.map(remove_entries, range(8)))

    assert len(store) == 0
    assert store.list() == []
