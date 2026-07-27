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