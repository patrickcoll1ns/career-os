from fastapi import UploadFile

from app.integrations.document_storage import LocalDocumentStorage
from app.models.document import Document
from app.repositories.documents import DocumentRepository


class DocumentService:
    """Coordinate document storage and its authoritative database record."""

    def __init__(
        self,
        repository: DocumentRepository,
        storage: LocalDocumentStorage,
    ) -> None:
        self.repository = repository
        self.storage = storage

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
            return await self.repository.add(document)
        except Exception:
            self.storage.delete(stored.storage_key)
            raise

    async def list_all(self) -> list[Document]:
        return await self.repository.list_all()
