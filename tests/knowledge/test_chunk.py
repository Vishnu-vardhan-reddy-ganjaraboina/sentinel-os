import pytest

from sentinel.knowledge.chunk import Chunk


def test_chunk_creation():
    chunk = Chunk(
        id="c1",
        document_id="doc1",
        text="Hello world",
        index=0,
    )

    assert chunk.id == "c1"
    assert chunk.document_id == "doc1"
    assert chunk.text == "Hello world"
    assert chunk.index == 0
    assert chunk.metadata == {}


def test_chunk_metadata():
    chunk = Chunk(
        id="c1",
        document_id="doc1",
        text="Hello",
        index=1,
        metadata={"page": "5"},
    )

    assert chunk.metadata["page"] == "5"


def test_empty_chunk_id():
    with pytest.raises(ValueError):
        Chunk(
            id="",
            document_id="doc1",
            text="abc",
            index=0,
        )


def test_empty_document_id():
    with pytest.raises(ValueError):
        Chunk(
            id="c1",
            document_id="",
            text="abc",
            index=0,
        )


def test_empty_text():
    with pytest.raises(ValueError):
        Chunk(
            id="c1",
            document_id="doc1",
            text="",
            index=0,
        )


def test_negative_index():
    with pytest.raises(ValueError):
        Chunk(
            id="c1",
            document_id="doc1",
            text="abc",
            index=-1,
        )