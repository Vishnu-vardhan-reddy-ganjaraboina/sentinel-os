from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class StorageItem:
    key: str
    value: Any