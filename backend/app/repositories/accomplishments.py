import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_owner_id
from app.models.accomplishment import Accomplishment


class AccomplishmentRepository:
    """Store and retrieve accomplishments through an asynchronous database session."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.owner_id = get_current_owner_id()

    async def add(self, accomplishment: Accomplishment) -> Accomplishment:
        accomplishment.owner_id = self.owner_id
        self.session.add(accomplishment)
        await self.session.commit()
        await self.session.refresh(accomplishment)
        return accomplishment

    async def list_all(self, *, include_archived: bool = False) -> list[Accomplishment]:
        query = (
            select(Accomplishment)
            .where(Accomplishment.owner_id == self.owner_id)
            .order_by(Accomplishment.created_at.desc())
        )
        if not include_archived:
            query = query.where(Accomplishment.archived_at.is_(None))

        result = await self.session.scalars(query)
        return list(result.all())

    async def list_archived(self) -> list[Accomplishment]:
        query = (
            select(Accomplishment)
            .where(
                Accomplishment.owner_id == self.owner_id,
                Accomplishment.archived_at.is_not(None),
            )
            .order_by(Accomplishment.archived_at.desc())
        )
        result = await self.session.scalars(query)
        return list(result.all())

    async def get(self, accomplishment_id: uuid.UUID) -> Accomplishment | None:
        return await self.session.scalar(
            select(Accomplishment).where(
                Accomplishment.id == accomplishment_id,
                Accomplishment.owner_id == self.owner_id,
            )
        )

    async def save(self, accomplishment: Accomplishment) -> Accomplishment:
        await self.session.commit()
        await self.session.refresh(accomplishment)
        return accomplishment

    async def delete(self, accomplishment: Accomplishment) -> None:
        await self.session.delete(accomplishment)
        await self.session.commit()
