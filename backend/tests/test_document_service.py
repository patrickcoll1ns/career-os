import asyncio
import uuid
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest

from app.integrations.document_chunker import DocumentChunker
from app.integrations.document_extractor import (
    DocumentExtractionError,
    DocumentTextExtractor,
)
from app.integrations.document_index import DocumentVectorIndex
from app.integrations.document_storage import (
    DocumentNotStoredError,
    LocalDocumentStorage,
    StoredDocument,
)
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
    vector_index.index.side_effect = RuntimeError("Embedding service unavailable")
    service = DocumentService(
        repository, storage, extractor, DocumentChunker(), vector_index
    )

    document = asyncio.run(service.upload(SimpleNamespace()))

    assert document.status == "failed"
    assert document.extracted_text == "Backend engineer"
    assert document.error_message == "Document vector indexing failed."


def build_service(**overrides):
    repository = overrides.get("repository") or AsyncMock(spec=DocumentRepository)
    storage = overrides.get("storage") or Mock(spec=LocalDocumentStorage)
    extractor = overrides.get("extractor") or Mock(spec=DocumentTextExtractor)
    vector_index = overrides.get("vector_index") or Mock(spec=DocumentVectorIndex)
    return (
        DocumentService(
            repository, storage, extractor, DocumentChunker(), vector_index
        ),
        repository,
        storage,
    )


def test_missing_stored_bytes_fail_the_document_instead_of_the_request() -> None:
    repository = AsyncMock(spec=DocumentRepository)
    repository.add.side_effect = lambda document: document
    repository.update.side_effect = lambda document: document
    storage = Mock(spec=LocalDocumentStorage)
    storage.save = AsyncMock(return_value=stored_document())
    storage.read = AsyncMock(side_effect=DocumentNotStoredError("Missing."))
    service, _, _ = build_service(repository=repository, storage=storage)

    document = asyncio.run(service.upload(SimpleNamespace()))

    assert document.status == "failed"
    assert document.error_message == "Missing."


def test_a_failed_database_write_removes_the_stored_object() -> None:
    repository = AsyncMock(spec=DocumentRepository)
    repository.add.side_effect = RuntimeError("database is down")
    storage = Mock(spec=LocalDocumentStorage)
    storage.save = AsyncMock(return_value=stored_document())
    storage.delete = AsyncMock()
    service, _, _ = build_service(repository=repository, storage=storage)

    with pytest.raises(RuntimeError):
        asyncio.run(service.upload(SimpleNamespace()))

    storage.delete.assert_awaited_once_with("document-id.txt")


def test_delete_removes_the_record_and_the_stored_object() -> None:
    document = SimpleNamespace(id=uuid.uuid4(), storage_key="document-id.txt")
    repository = AsyncMock(spec=DocumentRepository)
    repository.get.return_value = document
    storage = Mock(spec=LocalDocumentStorage)
    storage.delete = AsyncMock()
    service, _, _ = build_service(repository=repository, storage=storage)

    assert asyncio.run(service.delete(document.id)) is True

    repository.delete.assert_awaited_once_with(document)
    storage.delete.assert_awaited_once_with("document-id.txt")


def test_delete_reports_a_document_that_does_not_belong_to_the_owner() -> None:
    repository = AsyncMock(spec=DocumentRepository)
    repository.get.return_value = None
    service, _, storage = build_service(repository=repository)

    assert asyncio.run(service.delete(uuid.uuid4())) is False

    repository.delete.assert_not_awaited()


def test_delete_succeeds_even_when_object_storage_is_unreachable() -> None:
    document = SimpleNamespace(id=uuid.uuid4(), storage_key="document-id.txt")
    repository = AsyncMock(spec=DocumentRepository)
    repository.get.return_value = document
    storage = Mock(spec=LocalDocumentStorage)
    storage.delete = AsyncMock(side_effect=RuntimeError("bucket unreachable"))
    service, _, _ = build_service(repository=repository, storage=storage)

    assert asyncio.run(service.delete(document.id)) is True

    repository.delete.assert_awaited_once_with(document)
