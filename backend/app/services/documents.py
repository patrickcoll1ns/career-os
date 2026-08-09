import anyio
from fastapi import UploadFile

from app.integrations.document_extractor import (
    DocumentExtractionError,
    DocumentTextExtractor,
)
from app.integrations.document_storage import LocalDocumentStorage
from app.models.document import Document
from app.repositories.documents import DocumentRepository


class DocumentService:
    """Coordinate document storage and its authoritative database record."""

    def __init__(
        self,
        repository: DocumentRepository,
        storage: LocalDocumentStorage,
        extractor: DocumentTextExtractor,
    ) -> None:
        self.repository = repository
        self.storage = storage
        self.extractor = extractor

    async def upload(self, upload: UploadFile) -> Document:
        stored = await self.storage.save(upload)
        document = Document(
            original_filename=stored.original_filename,
            content_type=stored.content_type,
            size_bytes=stored.size_bytes,
            sha256=stored.sha256,
            storage_key=stored.storage_key,
            status="pending",
        )

        try:
            document = await self.repository.add(document)
        except Exception:
            self.storage.delete(stored.storage_key)
            raise

        document.status = "processing"
        document = await self.repository.update(document)

        try:
            extracted_text = await anyio.to_thread.run_sync(
                self.extractor.extract,
                self.storage.path_for(document.storage_key),
                document.content_type,
            )
        except DocumentExtractionError as error:
            document.status = "failed"
            document.error_message = str(error)
            return await self.repository.update(document)

        document.extracted_text = extracted_text
        document.error_message = None
        document.status = "ready"
        return await self.repository.update(document)

    async def list_all(self) -> list[Document]:
        return await self.repository.list_all()
