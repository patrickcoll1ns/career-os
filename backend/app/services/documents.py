import logging
import uuid

import anyio
from fastapi import UploadFile

from app.integrations.document_chunker import DocumentChunker
from app.integrations.document_extractor import (
    DocumentExtractionError,
    DocumentTextExtractor,
)
from app.integrations.document_index import DocumentVectorIndex
from app.integrations.document_storage import DocumentNotStoredError, DocumentStorage
from app.models.document import Document
from app.repositories.documents import DocumentRepository

logger = logging.getLogger("careeros.documents")


class DocumentService:
    """Coordinate document storage and its authoritative database record."""

    def __init__(
        self,
        repository: DocumentRepository,
        storage: DocumentStorage,
        extractor: DocumentTextExtractor,
        chunker: DocumentChunker,
        vector_index: DocumentVectorIndex,
    ) -> None:
        self.repository = repository
        self.storage = storage
        self.extractor = extractor
        self.chunker = chunker
        self.vector_index = vector_index

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
            await self.storage.delete(stored.storage_key)
            raise

        document.status = "processing"
        document = await self.repository.update(document)

        try:
            data = await self.storage.read(document.storage_key)
            extracted_text = await anyio.to_thread.run_sync(
                self.extractor.extract,
                data,
                document.content_type,
            )
        except (DocumentExtractionError, DocumentNotStoredError) as error:
            document.status = "failed"
            document.error_message = str(error)
            return await self.repository.update(document)

        document.extracted_text = extracted_text
        document.error_message = None
        chunks = self.chunker.split(extracted_text)

        try:
            await self.vector_index.index(
                document.id,
                document.original_filename,
                chunks,
            )
        except Exception:
            logger.exception(
                "Document indexing failed", extra={"document_id": str(document.id)}
            )
            document.status = "failed"
            document.error_message = "Document vector indexing failed."
            return await self.repository.update(document)

        document.status = "ready"
        return await self.repository.update(document)

    async def list_all(self) -> list[Document]:
        return await self.repository.list_all()

    async def delete(self, document_id: uuid.UUID) -> bool:
        """Remove a document, its embeddings, its reviews, and its stored bytes."""
        document = await self.repository.get(document_id)
        if document is None:
            return False

        storage_key = document.storage_key
        # Deleting the row cascades to document_chunks and resume_reviews, so the
        # database is consistent even if object storage is briefly unreachable.
        await self.repository.delete(document)

        try:
            await self.storage.delete(storage_key)
        except Exception:
            logger.exception(
                "Stored document bytes could not be deleted",
                extra={"document_id": str(document_id)},
            )
        return True
