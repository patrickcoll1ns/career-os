import asyncio
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

from app.integrations.document_chunker import DocumentChunker
from app.integrations.document_extractor import (
    DocumentExtractionError,
    DocumentTextExtractor,
)
from app.integrations.document_index import DocumentVectorIndex
from app.integrations.document_storage import LocalDocumentStorage, StoredDocument
from app.repositories.documents import DocumentRepository
from app.services.documents import DocumentService


def stored_document() -> StoredDocument:
    return StoredDocument(
        original_filename="resume.txt",
        content_type="text/plain",
        size_bytes=16,
        sha256="a" * 64,
        storage_key="document-id.txt",
    )


def test_successful_upload_stores_extracted_text_and_becomes_ready() -> None:
    repository = AsyncMock(spec=DocumentRepository)
    repository.add.side_effect = lambda document: document
    repository.update.side_effect = lambda document: document
    storage = Mock(spec=LocalDocumentStorage)
    storage.save = AsyncMock(return_value=stored_document())
    storage.path_for.return_value = Path("document-id.txt")
    extractor = Mock(spec=DocumentTextExtractor)
    extractor.extract.return_value = "Backend engineer"
    vector_index = Mock(spec=DocumentVectorIndex)
    service = DocumentService(
        repository, storage, extractor, DocumentChunker(), vector_index
    )

    document = asyncio.run(service.upload(SimpleNamespace()))

    assert document.status == "ready"
    assert document.extracted_text == "Backend engineer"
    assert repository.update.await_count == 2
    vector_index.index.assert_called_once()


def test_unreadable_upload_is_saved_with_a_failed_status() -> None:
    repository = AsyncMock(spec=DocumentRepository)
    repository.add.side_effect = lambda document: document
    repository.update.side_effect = lambda document: document
    storage = Mock(spec=LocalDocumentStorage)
    storage.save = AsyncMock(return_value=stored_document())
    storage.path_for.return_value = Path("document-id.txt")
    extractor = Mock(spec=DocumentTextExtractor)
    extractor.extract.side_effect = DocumentExtractionError("No readable text found.")
    vector_index = Mock(spec=DocumentVectorIndex)
    service = DocumentService(
        repository, storage, extractor, DocumentChunker(), vector_index
    )

    document = asyncio.run(service.upload(SimpleNamespace()))

    assert document.status == "failed"
    assert document.error_message == "No readable text found."
    assert document.extracted_text is None
    vector_index.index.assert_not_called()


def test_indexing_failure_saves_extracted_text_with_failed_status() -> None:
    repository = AsyncMock(spec=DocumentRepository)
    repository.add.side_effect = lambda document: document
    repository.update.side_effect = lambda document: document
    storage = Mock(spec=LocalDocumentStorage)
    storage.save = AsyncMock(return_value=stored_document())
    storage.path_for.return_value = Path("document-id.txt")
    extractor = Mock(spec=DocumentTextExtractor)
    extractor.extract.return_value = "Backend engineer"
    vector_index = Mock(spec=DocumentVectorIndex)
    vector_index.index.side_effect = RuntimeError("Chroma unavailable")
    service = DocumentService(
        repository, storage, extractor, DocumentChunker(), vector_index
    )

    document = asyncio.run(service.upload(SimpleNamespace()))

    assert document.status == "failed"
    assert document.extracted_text == "Backend engineer"
    assert document.error_message == "Document vector indexing failed."
