import uuid
from unittest.mock import Mock

from app.integrations.document_chunker import DocumentChunk
from app.integrations.document_index import DocumentVectorIndex


def build_index(client: Mock) -> DocumentVectorIndex:
    index = DocumentVectorIndex.__new__(DocumentVectorIndex)
    index.client = client
    index.collection_name = "career_documents"
    return index


def test_index_replaces_document_chunks_with_stable_ids_and_metadata() -> None:
    collection = Mock()
    client = Mock()
    client.get_or_create_collection.return_value = collection
    index = build_index(client)
    document_id = uuid.uuid4()
    chunks = [
        DocumentChunk(index=0, text="Python and FastAPI"),
        DocumentChunk(index=1, text="FastAPI and PostgreSQL"),
    ]

    index.index(document_id, "resume.pdf", chunks)

    client.get_or_create_collection.assert_called_once_with("career_documents")
    collection.delete.assert_called_once_with(where={"document_id": str(document_id)})
    collection.add.assert_called_once_with(
        ids=[f"{document_id}:0", f"{document_id}:1"],
        documents=["Python and FastAPI", "FastAPI and PostgreSQL"],
        metadatas=[
            {
                "document_id": str(document_id),
                "filename": "resume.pdf",
                "chunk_index": 0,
            },
            {
                "document_id": str(document_id),
                "filename": "resume.pdf",
                "chunk_index": 1,
            },
        ],
    )


def test_index_deletes_stale_records_when_document_has_no_chunks() -> None:
    collection = Mock()
    client = Mock()
    client.get_or_create_collection.return_value = collection
    index = build_index(client)

    index.index(uuid.uuid4(), "empty.txt", [])

    collection.delete.assert_called_once()
    collection.add.assert_not_called()
