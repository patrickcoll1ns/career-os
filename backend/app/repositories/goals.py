import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_owner_id
from app.models.goal import Goal


class GoalRepository:
    """Store and retrieve goals through an asynchronous database session."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.owner_id = get_current_owner_id()

    async def add(self, goal: Goal) -> Goal:
        goal.owner_id = self.owner_id
        self.session.add(goal)
        await self.session.commit()
        await self.session.refresh(goal)
        return goal

    async def list_all(self, *, include_archived: bool = False) -> list[Goal]:
        query = (
            select(Goal)
            .where(Goal.owner_id == self.owner_id)
            .order_by(Goal.created_at.desc())
        )
        if not include_archived:
            query = query.where(Goal.archived_at.is_(None))

        result = await self.session.scalars(query)
        return list(result.all())

    async def list_archived(self) -> list[Goal]:
        query = (
            select(Goal)
            .where(Goal.owner_id == self.owner_id, Goal.archived_at.is_not(None))
            .order_by(Goal.archived_at.desc())
        )
        result = await self.session.scalars(query)
        return list(result.all())

    async def get(self, goal_id: uuid.UUID) -> Goal | None:
        return await self.session.scalar(
            select(Goal).where(Goal.id == goal_id, Goal.owner_id == self.owner_id)
        )

    async def save(self, goal: Goal) -> Goal:
        await self.session.commit()
        await self.session.refresh(goal)
        return goal

    async def delete(self, goal: Goal) -> None:
        await self.session.delete(goal)
        await self.session.commit()
