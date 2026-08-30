import uuid
from unittest.mock import AsyncMock, Mock

import pytest

from app.integrations.document_chunker import DocumentChunk
from app.integrations.document_index import DocumentVectorIndex
from app.models.document_chunk import DocumentChunkRecord

OWNER_ID = "google:123"


def build_index(
    session: AsyncMock, embedder: Mock | None = None
) -> DocumentVectorIndex:
    index = DocumentVectorIndex.__new__(DocumentVectorIndex)
    index.session = session
    index.embedder = embedder or Mock()
    index.owner_id = OWNER_ID
    index.max_distance = 0.6
    return index


def build_embedder(vectors: list[list[float]]) -> Mock:
    embedder = Mock()
    embedder.is_configured = True
    embedder.embed_documents = AsyncMock(return_value=vectors)
    embedder.embed_query = AsyncMock(return_value=vectors[0] if vectors else [0.0])
    return embedder


async def test_index_replaces_chunks_with_owner_scoped_rows() -> None:
    session = AsyncMock()
    session.add_all = Mock()
    embedder = build_embedder([[0.1, 0.2], [0.3, 0.4]])
    index = build_index(session, embedder)
    document_id = uuid.uuid4()
    chunks = [
        DocumentChunk(index=0, text="Python and FastAPI"),
        DocumentChunk(index=1, text="FastAPI and PostgreSQL"),
    ]

    await index.index(document_id, "resume.pdf", chunks)

    # Existing rows are cleared before new ones are written.
    session.execute.assert_awaited_once()
    embedder.embed_documents.assert_awaited_once_with(
        ["Python and FastAPI", "FastAPI and PostgreSQL"]
    )
    added = session.add_all.call_args.args[0]
    assert [record.chunk_index for record in added] == [0, 1]
    assert {record.owner_id for record in added} == {OWNER_ID}
    assert {record.document_id for record in added} == {document_id}
    assert [record.embedding for record in added] == [[0.1, 0.2], [0.3, 0.4]]
    session.commit.assert_awaited()


async def test_index_only_deletes_when_a_document_has_no_chunks() -> None:
    session = AsyncMock()
    session.add_all = Mock()
    embedder = build_embedder([])
    index = build_index(session, embedder)

    await index.index(uuid.uuid4(), "empty.txt", [])

    session.execute.assert_awaited_once()
    session.add_all.assert_not_called()
    embedder.embed_documents.assert_not_awaited()
    session.commit.assert_awaited_once()


async def test_search_returns_typed_chunks_with_source_metadata() -> None:
    document_id = uuid.uuid4()
    record = DocumentChunkRecord(
        owner_id=OWNER_ID,
        document_id=document_id,
        chunk_index=3,
        filename="resume.pdf",
        text="Built production APIs with FastAPI",
        embedding=[0.1],
    )
    session = AsyncMock()
    session.execute.return_value = Mock(all=Mock(return_value=[(record, 0.21)]))
    index = build_index(session, build_embedder([[0.1]]))

    chunks = await index.search("backend experience", limit=4)

    assert len(chunks) == 1
    assert chunks[0].document_id == str(document_id)
    assert chunks[0].filename == "resume.pdf"
    assert chunks[0].chunk_index == 3
    assert chunks[0].text == "Built production APIs with FastAPI"
    assert chunks[0].distance == pytest.approx(0.21)


async def test_search_returns_an_empty_list_when_nothing_is_indexed() -> None:
    session = AsyncMock()
    session.execute.return_value = Mock(all=Mock(return_value=[]))

    assert await build_index(session, build_embedder([[0.1]])).search("anything") == []


async def test_search_is_skipped_when_no_embedding_key_is_configured() -> None:
    session = AsyncMock()
    embedder = Mock()
    embedder.is_configured = False
    embedder.embed_query = AsyncMock()

    assert await build_index(session, embedder).search("anything") == []

    session.execute.assert_not_awaited()
    embedder.embed_query.assert_not_awaited()


async def test_delete_document_clears_only_that_document() -> None:
    session = AsyncMock()
    index = build_index(session, build_embedder([[0.1]]))

    await index.delete_document(uuid.uuid4())

    session.execute.assert_awaited_once()
    session.commit.assert_awaited_once()


async def test_indexing_is_skipped_when_no_embedding_key_is_configured() -> None:
    """A missing Voyage key must not fail the upload.

    The document stays usable for resume review; only copilot retrieval is off.
    """
    session = AsyncMock()
    session.add_all = Mock()
    embedder = Mock()
    embedder.is_configured = False
    embedder.embed_documents = AsyncMock()
    index = build_index(session, embedder)

    await index.index(uuid.uuid4(), "resume.pdf", [DocumentChunk(index=0, text="Hi")])

    embedder.embed_documents.assert_not_awaited()
    session.add_all.assert_not_called()
    session.commit.assert_awaited_once()
