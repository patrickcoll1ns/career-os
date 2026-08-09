import pytest

from app.integrations.document_chunker import DocumentChunker


def test_short_text_stays_in_one_chunk() -> None:
    chunks = DocumentChunker(max_characters=100, overlap_characters=20).split(
        "Python FastAPI PostgreSQL"
    )

    assert [chunk.text for chunk in chunks] == ["Python FastAPI PostgreSQL"]
    assert chunks[0].index == 0


def test_long_text_is_bounded_and_overlapping() -> None:
    chunks = DocumentChunker(max_characters=25, overlap_characters=10).split(
        "alpha beta gamma delta epsilon zeta eta theta"
    )

    assert len(chunks) > 1
    assert all(len(chunk.text) <= 25 for chunk in chunks)
    assert chunks[0].text.split()[-1] == chunks[1].text.split()[0]
    assert [chunk.index for chunk in chunks] == list(range(len(chunks)))


def test_whitespace_is_normalized() -> None:
    chunks = DocumentChunker().split("  Python\n\nFastAPI\tPostgreSQL  ")

    assert chunks[0].text == "Python FastAPI PostgreSQL"


def test_empty_text_produces_no_chunks() -> None:
    assert DocumentChunker().split(" \n\t ") == []


@pytest.mark.parametrize(
    ("max_characters", "overlap_characters"),
    [(0, 0), (100, -1), (100, 100), (100, 101)],
)
def test_invalid_chunk_settings_are_rejected(
    max_characters: int,
    overlap_characters: int,
) -> None:
    with pytest.raises(ValueError):
        DocumentChunker(max_characters, overlap_characters)
