import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
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
    include_archived: bool = False,
) -> list[AccomplishmentRead]:
    accomplishments = await service.list_all(include_archived=include_archived)
    return [AccomplishmentRead.model_validate(a) for a in accomplishments]


@router.get("/archived", response_model=list[AccomplishmentRead])
async def list_archived_accomplishments(
    service: AccomplishmentServiceDependency,
) -> list[AccomplishmentRead]:
    accomplishments = await service.list_archived()
    return [AccomplishmentRead.model_validate(a) for a in accomplishments]


@router.post("/{accomplishment_id}/archive", response_model=AccomplishmentRead)
async def archive_accomplishment(
    accomplishment_id: uuid.UUID,
    service: AccomplishmentServiceDependency,
) -> AccomplishmentRead:
    accomplishment = await service.archive(accomplishment_id)
    if accomplishment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Accomplishment not found",
        )

    return AccomplishmentRead.model_validate(accomplishment)


@router.post("/{accomplishment_id}/restore", response_model=AccomplishmentRead)
async def restore_accomplishment(
    accomplishment_id: uuid.UUID,
    service: AccomplishmentServiceDependency,
) -> AccomplishmentRead:
    accomplishment = await service.restore(accomplishment_id)
    if accomplishment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Accomplishment not found",
        )

    return AccomplishmentRead.model_validate(accomplishment)


@router.delete("/{accomplishment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_accomplishment(
    accomplishment_id: uuid.UUID,
    service: AccomplishmentServiceDependency,
) -> Response:
    """Permanently remove an accomplishment. Archiving is the recoverable option."""
    if not await service.delete(accomplishment_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Accomplishment not found",
        )

    return Response(status_code=status.HTTP_204_NO_CONTENT)
