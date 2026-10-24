from concurrent.futures import ThreadPoolExecutor

from sentinel.memory.constants import MemoryStatus
from sentinel.memory.entry import BaseMemoryEntry


def test_concurrent_entry_lifecycle_operations_remain_consistent() -> None:
    entry = BaseMemoryEntry("memory.concurrent", {"value": 1})

    def operate(operation: str) -> None:
        if operation == "touch":
            entry.touch()
        elif operation == "archive":
            entry.archive()
        elif operation == "delete":
            entry.delete()
        elif operation == "status":
            _ = entry.status
        elif operation == "dict":
            _ = entry.to_dict()

    operations = ["touch", "archive", "delete", "status", "dict"] * 100

    with ThreadPoolExecutor(max_workers=16) as pool:
        list(pool.map(operate, operations))

    assert entry.status in {MemoryStatus.ARCHIVED, MemoryStatus.DELETED}
