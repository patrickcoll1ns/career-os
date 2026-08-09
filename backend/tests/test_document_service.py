import asyncio
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

from app.integrations.document_extractor import (
    DocumentExtractionError,
    DocumentTextExtractor,
)
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
    service = DocumentService(repository, storage, extractor)

    document = asyncio.run(service.upload(SimpleNamespace()))

    assert document.status == "ready"
    assert document.extracted_text == "Backend engineer"
    assert repository.update.await_count == 2


def test_unreadable_upload_is_saved_with_a_failed_status() -> None:
    repository = AsyncMock(spec=DocumentRepository)
    repository.add.side_effect = lambda document: document
    repository.update.side_effect = lambda document: document
    storage = Mock(spec=LocalDocumentStorage)
    storage.save = AsyncMock(return_value=stored_document())
    storage.path_for.return_value = Path("document-id.txt")
    extractor = Mock(spec=DocumentTextExtractor)
    extractor.extract.side_effect = DocumentExtractionError("No readable text found.")
    service = DocumentService(repository, storage, extractor)

    document = asyncio.run(service.upload(SimpleNamespace()))

    assert document.status == "failed"
    assert document.error_message == "No readable text found."
    assert document.extracted_text is None
