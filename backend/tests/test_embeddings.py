import pytest

from app.core.config import settings
from app.integrations.embeddings import (
    MAX_TEXTS_PER_REQUEST,
    EmbeddingError,
    VoyageEmbedder,
)


def build_embedder(dimensions: int = 2) -> VoyageEmbedder:
    return VoyageEmbedder(api_key="test-key", model="voyage-3.5", dimensions=dimensions)


def test_results_are_ordered_by_the_index_voyage_returns() -> None:
    body = {
        "data": [
            {"index": 1, "embedding": [0.3, 0.4]},
            {"index": 0, "embedding": [0.1, 0.2]},
        ]
    }

    assert build_embedder()._parse(body, 2) == [[0.1, 0.2], [0.3, 0.4]]


def test_a_wrong_vector_count_is_rejected() -> None:
    with pytest.raises(EmbeddingError, match="malformed"):
        build_embedder()._parse({"data": [{"index": 0, "embedding": [0.1, 0.2]}]}, 2)


def test_a_wrong_vector_width_is_rejected() -> None:
    with pytest.raises(EmbeddingError, match="dimensions"):
        build_embedder()._parse({"data": [{"index": 0, "embedding": [0.1]}]}, 1)


async def test_an_unconfigured_key_is_reported_before_any_request(
    monkeypatch,
) -> None:
    monkeypatch.setattr(settings, "voyage_api_key", None)
    embedder = VoyageEmbedder()

    assert not embedder.is_configured
    with pytest.raises(EmbeddingError, match="VOYAGE_API_KEY"):
        await embedder.embed_documents(["anything"])


async def test_no_request_is_made_for_an_empty_batch() -> None:
    assert await build_embedder().embed_documents([]) == []


async def test_large_inputs_are_split_into_bounded_batches(monkeypatch) -> None:
    embedder = build_embedder()
    batch_sizes: list[int] = []

    async def fake_batch(_client, batch, _input_type):
        batch_sizes.append(len(batch))
        return [[0.1, 0.2] for _ in batch]

    monkeypatch.setattr(embedder, "_embed_batch", fake_batch)
    texts = [f"chunk {index}" for index in range(MAX_TEXTS_PER_REQUEST + 5)]

    vectors = await embedder.embed_documents(texts)

    assert len(vectors) == len(texts)
    assert batch_sizes == [MAX_TEXTS_PER_REQUEST, 5]
