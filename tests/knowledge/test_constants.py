from sentinel.knowledge.constants import (
    DEFAULT_CHUNK_OVERLAP,
    DEFAULT_CHUNK_SIZE,
    DEFAULT_EMBEDDING_DIMENSION,
    DEFAULT_SEARCH_LIMIT,
)


def test_constants():
    assert DEFAULT_SEARCH_LIMIT == 5
    assert DEFAULT_EMBEDDING_DIMENSION == 384
    assert DEFAULT_CHUNK_SIZE == 512
    assert DEFAULT_CHUNK_OVERLAP == 64