from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.accomplishment import Accomplishment


class AccomplishmentRepository:
    """Store and retrieve accomplishments through an asynchronous database session."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add(self, accomplishment: Accomplishment) -> Accomplishment:
        self.session.add(accomplishment)
        await self.session.commit()
        await self.session.refresh(accomplishment)
        return accomplishment

    async def list_all(self) -> list[Accomplishment]:
        result = await self.session.scalars(
            select(Accomplishment).order_by(Accomplishment.created_at.desc())
        )
        return list(result.all())
