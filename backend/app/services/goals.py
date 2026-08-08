import uuid
from datetime import UTC, datetime

from app.models.goal import Goal
from app.repositories.goals import GoalRepository
from app.schemas.goal import GoalCreate, GoalStatus, GoalUpdate


class GoalService:
    """Coordinate goal-related application actions."""

    def __init__(self, repository: GoalRepository) -> None:
        self.repository = repository

    async def create(self, goal_data: GoalCreate) -> Goal:
        goal = Goal(
            title=goal_data.title,
            description=goal_data.description,
            target_date=goal_data.target_date,
        )
        return await self.repository.add(goal)

    async def list_all(self, *, include_archived: bool = False) -> list[Goal]:
        return await self.repository.list_all(include_archived=include_archived)

    async def list_archived(self) -> list[Goal]:
        return await self.repository.list_archived()

    async def update(
        self,
        goal_id: uuid.UUID,
        goal_data: GoalUpdate,
    ) -> Goal | None:
        goal = await self.repository.get(goal_id)
        if goal is None:
            return None

        updates = goal_data.model_dump(exclude_unset=True)
        if isinstance(updates.get("status"), GoalStatus):
            updates["status"] = updates["status"].value

        for field, value in updates.items():
            setattr(goal, field, value)

        return await self.repository.save(goal)

    async def archive(self, goal_id: uuid.UUID) -> Goal | None:
        goal = await self.repository.get(goal_id)
        if goal is None:
            return None

        goal.archived_at = datetime.now(UTC)
        return await self.repository.save(goal)

    async def restore(self, goal_id: uuid.UUID) -> Goal | None:
        goal = await self.repository.get(goal_id)
        if goal is None:
            return None

        goal.archived_at = None
        return await self.repository.save(goal)
