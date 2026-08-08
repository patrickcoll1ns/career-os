import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.goal import Goal


class GoalRepository:
    """Store and retrieve goals through an asynchronous database session."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add(self, goal: Goal) -> Goal:
        self.session.add(goal)
        await self.session.commit()
        await self.session.refresh(goal)
        return goal

    async def list_all(self) -> list[Goal]:
        result = await self.session.scalars(
            select(Goal).order_by(Goal.created_at.desc())
        )
        return list(result.all())

    async def get(self, goal_id: uuid.UUID) -> Goal | None:
        return await self.session.get(Goal, goal_id)

    async def save(self, goal: Goal) -> Goal:
        await self.session.commit()
        await self.session.refresh(goal)
        return goal
