from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import get_database_session
from app.integrations.document_chunker import DocumentChunker
from app.integrations.document_extractor import DocumentTextExtractor
from app.integrations.document_index import DocumentVectorIndex
from app.integrations.document_storage import (
    DocumentTooLargeError,
    InvalidDocumentError,
    LocalDocumentStorage,
)
from app.repositories.documents import DocumentRepository
from app.schemas.document import DocumentRead
from app.services.documents import DocumentService

router = APIRouter(prefix="/documents", tags=["documents"])
DatabaseSession = Annotated[AsyncSession, Depends(get_database_session)]


def get_document_service(session: DatabaseSession) -> DocumentService:
    return DocumentService(
        DocumentRepository(session),
        LocalDocumentStorage(
            settings.document_upload_directory,
            settings.max_document_size_bytes,
        ),
        DocumentTextExtractor(),
        DocumentChunker(),
        DocumentVectorIndex(
            settings.chroma_host,
            settings.chroma_port,
            settings.chroma_collection,
            settings.chroma_max_distance,
        ),
    )


DocumentServiceDependency = Annotated[DocumentService, Depends(get_document_service)]


@router.post("", response_model=DocumentRead, status_code=status.HTTP_201_CREATED)
async def upload_document(
    service: DocumentServiceDependency,
    file: Annotated[UploadFile, File(description="PDF, DOCX, or TXT; maximum 5 MB")],
) -> DocumentRead:
    try:
        document = await service.upload(file)
    except DocumentTooLargeError as error:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail=str(error),
        ) from error
    except InvalidDocumentError as error:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=str(error),
        ) from error
    return DocumentRead.model_validate(document)


@router.get("", response_model=list[DocumentRead])
async def list_documents(
    service: DocumentServiceDependency,
) -> list[DocumentRead]:
    documents = await service.list_all()
    return [DocumentRead.model_validate(document) for document in documents]
