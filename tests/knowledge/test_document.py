import pytest

from sentinel.knowledge.document import Document


def test_document_creation():
    doc = Document(
        id="1",
        text="Hello Sentinel",
    )

    assert doc.id == "1"
    assert doc.text == "Hello Sentinel"
    assert doc.metadata == {}


def test_document_metadata():
    doc = Document(
        id="1",
        text="Knowledge",
        metadata={"source": "manual"},
    )

    assert doc.metadata["source"] == "manual"


def test_empty_id():
    with pytest.raises(ValueError):
        Document(
            id="",
            text="abc",
        )


def test_empty_text():
    with pytest.raises(ValueError):
        Document(
            id="1",
            text="",
        )