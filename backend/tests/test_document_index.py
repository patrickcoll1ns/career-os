import uuid
from unittest.mock import Mock

from app.integrations.document_chunker import DocumentChunk
from app.integrations.document_index import DocumentVectorIndex


def build_index(client: Mock) -> DocumentVectorIndex:
    index = DocumentVectorIndex.__new__(DocumentVectorIndex)
    index.client = client
    index.collection_name = "career_documents"
    index.max_distance = 1.6
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


def test_search_returns_typed_chunks_with_source_metadata() -> None:
    collection = Mock()
    collection.query.return_value = {
        "documents": [["Built production APIs with FastAPI"]],
        "metadatas": [
            [
                {
                    "document_id": "document-1",
                    "filename": "resume.pdf",
                    "chunk_index": 3,
                }
            ]
        ],
        "distances": [[0.72]],
    }
    client = Mock()
    client.get_or_create_collection.return_value = collection
    index = build_index(client)

    chunks = index.search("backend experience", limit=4)

    collection.query.assert_called_once_with(
        query_texts=["backend experience"],
        n_results=4,
        include=["documents", "metadatas", "distances"],
    )
    assert len(chunks) == 1
    assert chunks[0].document_id == "document-1"
    assert chunks[0].filename == "resume.pdf"
    assert chunks[0].chunk_index == 3
    assert chunks[0].text == "Built production APIs with FastAPI"
    assert chunks[0].distance == 0.72


def test_search_returns_empty_list_for_an_empty_collection() -> None:
    collection = Mock()
    collection.query.return_value = {
        "documents": [[]],
        "metadatas": [[]],
        "distances": [[]],
    }
    client = Mock()
    client.get_or_create_collection.return_value = collection

    assert build_index(client).search("anything") == []


def test_search_filters_chunks_above_the_relevance_distance() -> None:
    collection = Mock()
    collection.query.return_value = {
        "documents": [["Relevant resume text", "Unrelated resume text"]],
        "metadatas": [
            [
                {
                    "document_id": "document-1",
                    "filename": "resume.pdf",
                    "chunk_index": 0,
                },
                {
                    "document_id": "document-1",
                    "filename": "resume.pdf",
                    "chunk_index": 1,
                },
            ]
        ],
        "distances": [[1.2, 1.7]],
    }
    client = Mock()
    client.get_or_create_collection.return_value = collection

    chunks = build_index(client).search("backend experience")

    assert [chunk.text for chunk in chunks] == ["Relevant resume text"]
