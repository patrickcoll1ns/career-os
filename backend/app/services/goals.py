from app.models.goal import Goal
from app.repositories.goals import GoalRepository
from app.schemas.goal import GoalCreate


class GoalService:
    """Coordinate goal-related application actions."""

    def __init__(self, repository: GoalRepository) -> None:
        self.repository = repository

    async def create(self, goal_data: GoalCreate) -> Goal:
        goal = Goal(
            title=goal_data.title.strip(),
            description=goal_data.description,
            target_date=goal_data.target_date,
        )
        return await self.repository.add(goal)

    async def list_all(self) -> list[Goal]:
        return await self.repository.list_all()
