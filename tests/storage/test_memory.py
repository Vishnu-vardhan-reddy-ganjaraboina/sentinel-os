from sentinel.storage.backends.memory import MemoryBackend


def test_memory_backend() -> None:
    backend = MemoryBackend()

    backend.connect()

    backend.save("language", "Python")

    assert backend.exists("language")
    assert backend.load("language") == "Python"

    backend.delete("language")

    assert not backend.exists("language")

    backend.disconnect()