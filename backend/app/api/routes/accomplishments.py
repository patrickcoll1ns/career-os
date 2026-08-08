from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_database_session
from app.repositories.accomplishments import AccomplishmentRepository
from app.schemas.accomplishment import AccomplishmentCreate, AccomplishmentRead
from app.services.accomplishments import AccomplishmentService

router = APIRouter(prefix="/accomplishments", tags=["accomplishments"])
DatabaseSession = Annotated[AsyncSession, Depends(get_database_session)]


def get_accomplishment_service(session: DatabaseSession) -> AccomplishmentService:
    return AccomplishmentService(AccomplishmentRepository(session))


AccomplishmentServiceDependency = Annotated[
    AccomplishmentService, Depends(get_accomplishment_service)
]


@router.post("", response_model=AccomplishmentRead, status_code=status.HTTP_201_CREATED)
async def create_accomplishment(
    accomplishment_data: AccomplishmentCreate,
    service: AccomplishmentServiceDependency,
) -> AccomplishmentRead:
    accomplishment = await service.create(accomplishment_data)
    return AccomplishmentRead.model_validate(accomplishment)


@router.get("", response_model=list[AccomplishmentRead])
async def list_accomplishments(
    service: AccomplishmentServiceDependency,
) -> list[AccomplishmentRead]:
    accomplishments = await service.list_all()
    return [AccomplishmentRead.model_validate(a) for a in accomplishments]
