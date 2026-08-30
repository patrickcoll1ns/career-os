import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_owner_id
from app.models.document import Document


class DocumentRepository:
    """Store and retrieve document records through an async database session."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.owner_id = get_current_owner_id()

    async def add(self, document: Document) -> Document:
        document.owner_id = self.owner_id
        return await self._save(document)

    async def update(self, document: Document) -> Document:
        return await self._save(document)

    async def get(self, document_id: uuid.UUID) -> Document | None:
        return await self.session.scalar(
            select(Document).where(
                Document.id == document_id,
                Document.owner_id == self.owner_id,
            )
        )

    async def delete(self, document: Document) -> None:
        await self.session.delete(document)
        await self.session.commit()

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
            select(Document)
            .order_by(Document.created_at.desc())
            .where(Document.owner_id == self.owner_id)
        )
        return list(result.all())
