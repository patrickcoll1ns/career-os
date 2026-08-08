import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_database_session
from app.repositories.goals import GoalRepository
from app.schemas.goal import GoalCreate, GoalRead, GoalUpdate
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
async def list_goals(
    service: GoalServiceDependency,
    include_archived: bool = False,
) -> list[GoalRead]:
    goals = await service.list_all(include_archived=include_archived)
    return [GoalRead.model_validate(goal) for goal in goals]


@router.patch("/{goal_id}", response_model=GoalRead)
async def update_goal(
    goal_id: uuid.UUID,
    goal_data: GoalUpdate,
    service: GoalServiceDependency,
) -> GoalRead:
    goal = await service.update(goal_id, goal_data)
    if goal is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Goal not found",
        )

    return GoalRead.model_validate(goal)


@router.post("/{goal_id}/archive", response_model=GoalRead)
async def archive_goal(
    goal_id: uuid.UUID,
    service: GoalServiceDependency,
) -> GoalRead:
    goal = await service.archive(goal_id)
    if goal is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Goal not found",
        )

    return GoalRead.model_validate(goal)
