from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_database_session
from app.repositories.goals import GoalRepository
from app.schemas.goal import GoalCreate, GoalRead
from app.services.goals import GoalService


router = APIRouter(prefix="/goals", tags=["goals"])
DatabaseSession = Annotated[AsyncSession, Depends(get_database_session)]


def get_goal_service(session: DatabaseSession) -> GoalService:
    return GoalService(GoalRepository(session))


GoalServiceDependency = Annotated[GoalService, Depends(get_goal_service)]


@router.post("", response_model=GoalRead, status_code=status.HTTP_201_CREATED)
async def create_goal(
    goal_data: GoalCreate,
    service: GoalServiceDependency,
) -> GoalRead:
    goal = await service.create(goal_data)
    return GoalRead.model_validate(goal)


@router.get("", response_model=list[GoalRead])
async def list_goals(service: GoalServiceDependency) -> list[GoalRead]:
    goals = await service.list_all()
    return [GoalRead.model_validate(goal) for goal in goals]
