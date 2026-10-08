from sentinel.memory.entry import BaseMemoryEntry


def test_constructor_isolates_original_content() -> None:
    content = {
        "user": {
            "name": "Sentinel",
            "preferences": {
                "language": "en",
            },
        }
    }

    entry = BaseMemoryEntry(
        memory_id="memory.constructor",
        content=content,
    )

    content["user"]["preferences"]["language"] = "modified"

    assert entry.content["user"]["preferences"]["language"] == "en"
