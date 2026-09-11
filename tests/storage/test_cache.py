from sentinel.storage.cache import LRUCache


def test_put_get():
    cache = LRUCache[str, int](2)

    cache.put("a", 1)

    assert cache.get("a") == 1


def test_missing_key():
    cache = LRUCache[str, int](2)

    assert cache.get("x") is None


def test_eviction():
    cache = LRUCache[str, int](2)

    cache.put("a", 1)
    cache.put("b", 2)
    cache.put("c", 3)

    assert "a" not in cache
    assert "b" in cache
    assert "c" in cache


def test_recently_used():
    cache = LRUCache[str, int](2)

    cache.put("a", 1)
    cache.put("b", 2)

    cache.get("a")

    cache.put("c", 3)

    assert "a" in cache
    assert "b" not in cache


def test_clear():
    cache = LRUCache[str, int](4)

    cache.put("x", 1)
    cache.put("y", 2)

    cache.clear()

    assert len(cache) == 0


def test_invalid_capacity():
    import pytest

    with pytest.raises(ValueError):
        LRUCache(0)

import threading


def test_invalid_capacity_type():
    import pytest

    with pytest.raises(TypeError):
        LRUCache("2")  # type: ignore[arg-type]


def test_put_get_isolation():
    cache = LRUCache[str, dict](2)

    value = {
        "name": "Sentinel",
        "version": 1,
    }

    cache.put("config", value)

    value["version"] = 99

    assert cache.get("config")["version"] == 1


def test_returned_value_is_copy():
    cache = LRUCache[str, list[int]](2)

    cache.put("numbers", [1, 2, 3])

    result = cache.get("numbers")

    assert result is not None

    result.append(4)

    assert cache.get("numbers") == [1, 2, 3]


def test_capacity_property():
    cache = LRUCache[str, int](5)

    assert cache.capacity == 5


def test_concurrent_puts():
    cache = LRUCache[int, int](100)

    def writer(start: int) -> None:
        for index in range(start, start + 20):
            cache.put(index, index)

    threads = [
        threading.Thread(
            target=writer,
            args=(offset,),
        )
        for offset in range(0, 100, 20)
    ]

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()

    assert len(cache) == 100

    for index in range(100):
        assert cache.get(index) == index