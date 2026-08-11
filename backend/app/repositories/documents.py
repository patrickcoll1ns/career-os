import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document


class DocumentRepository:
    """Store and retrieve document records through an async database session."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add(self, document: Document) -> Document:
        return await self._save(document)

    async def update(self, document: Document) -> Document:
        return await self._save(document)

    async def get(self, document_id: uuid.UUID) -> Document | None:
        return await self.session.get(Document, document_id)

    async def _save(self, document: Document) -> Document:
        self.session.add(document)
        try:
            await self.session.commit()
        except Exception:
            await self.session.rollback()
            raise
        await self.session.refresh(document)
        return document

    async def list_all(self) -> list[Document]:
        result = await self.session.scalars(
            select(Document).order_by(Document.created_at.desc())
        )
        return list(result.all())
