"""
Tests for Sentinel Knowledge document chunking.
"""

from concurrent.futures import ThreadPoolExecutor

import pytest

from sentinel.knowledge.chunker import FixedSizeChunker
from sentinel.knowledge.document import Document


def test_chunk_small_document() -> None:
    chunker = FixedSizeChunker(
        chunk_size=10,
        overlap=2,
    )

    chunks = chunker.chunk(
        Document(
            id="doc1",
            text="Hello",
        )
    )

    assert len(chunks) == 1
    assert chunks[0].id == "doc1:0"
    assert chunks[0].document_id == "doc1"
    assert chunks[0].text == "Hello"
    assert chunks[0].index == 0


def test_chunk_large_document() -> None:
    chunker = FixedSizeChunker(
        chunk_size=5,
        overlap=2,
    )

    chunks = chunker.chunk(
        Document(
            id="doc1",
            text="ABCDEFGHIJ",
        )
    )

    assert [chunk.text for chunk in chunks] == [
        "ABCDE",
        "DEFGH",
        "GHIJ",
    ]

    assert [chunk.index for chunk in chunks] == [
        0,
        1,
        2,
    ]

    assert [chunk.id for chunk in chunks] == [
        "doc1:0",
        "doc1:1",
        "doc1:2",
    ]


def test_chunk_copies_metadata() -> None:
    document = Document(
        id="doc1",
        text="Hello",
        metadata={
            "source": "test",
        },
    )

    chunker = FixedSizeChunker()

    chunks = chunker.chunk(document)

    assert chunks[0].metadata == {
        "source": "test",
    }

    assert chunks[0].metadata is not document.metadata


@pytest.mark.parametrize(
    ("chunk_size", "overlap"),
    [
        (0, 0),
        (-1, 0),
        (10, -1),
        (10, 10),
        (10, 11),
    ],
)
def test_invalid_configuration(
    chunk_size: int,
    overlap: int,
) -> None:
    with pytest.raises(ValueError):
        FixedSizeChunker(
            chunk_size=chunk_size,
            overlap=overlap,
        )


def test_chunk_concurrently() -> None:
    chunker = FixedSizeChunker(
        chunk_size=10,
        overlap=2,
    )

    documents = [
        Document(
            id=f"doc-{index}",
            text=f"Document {index} contains Sentinel knowledge.",
        )
        for index in range(20)
    ]

    def chunk_document(
        document: Document,
    ) -> tuple[str, list[str]]:
        chunks = chunker.chunk(document)

        return (
            document.id,
            [chunk.text for chunk in chunks],
        )

    with ThreadPoolExecutor(max_workers=8) as executor:
        results = list(
            executor.map(
                chunk_document,
                documents,
            )
        )

    assert len(results) == len(documents)

    for document, result in zip(
        documents,
        results,
        strict=True,
    ):
        document_id, chunks = result

        assert document_id == document.id
        assert chunks

        sequential = [
            chunk.text
            for chunk in chunker.chunk(document)
        ]

        assert chunks == sequential