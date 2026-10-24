from sentinel.memory.entry import BaseMemoryEntry


def test_constructor_isolates_original_content() -> None:
    content = {"user": {"preferences": {"language": "en"}}}
    entry = BaseMemoryEntry("memory.constructor", content)

    content["user"]["preferences"]["language"] = "modified"

    assert entry.content["user"]["preferences"]["language"] == "en"


def test_content_property_returns_isolated_content() -> None:
    entry = BaseMemoryEntry(
        "memory.read",
        {"preferences": {"language": "en"}},
    )

    returned_content = entry.content
    returned_content["preferences"]["language"] = "modified"

    assert entry.content["preferences"]["language"] == "en"


def test_to_dict_returns_isolated_content() -> None:
    entry = BaseMemoryEntry(
        "memory.dict",
        {"preferences": {"language": "en"}},
    )

    result = entry.to_dict()
    result["content"]["preferences"]["language"] = "modified"

    assert entry.content["preferences"]["language"] == "en"
