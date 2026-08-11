import uuid
from datetime import UTC, datetime

from app.models.accomplishment import Accomplishment
from app.repositories.accomplishments import AccomplishmentRepository
from app.schemas.accomplishment import AccomplishmentCreate


class AccomplishmentService:
    """Coordinate accomplishment-related application actions."""

    def __init__(self, repository: AccomplishmentRepository) -> None:
        self.repository = repository

    async def create(self, data: AccomplishmentCreate) -> Accomplishment:
        accomplishment = Accomplishment(
            title=data.title,
            description=data.description,
            achieved_on=data.achieved_on,
        )
        return await self.repository.add(accomplishment)

    async def list_all(self, *, include_archived: bool = False) -> list[Accomplishment]:
        return await self.repository.list_all(include_archived=include_archived)

    async def list_archived(self) -> list[Accomplishment]:
        return await self.repository.list_archived()

    async def archive(self, accomplishment_id: uuid.UUID) -> Accomplishment | None:
        accomplishment = await self.repository.get(accomplishment_id)
        if accomplishment is None:
            return None

        accomplishment.archived_at = datetime.now(UTC)
        return await self.repository.save(accomplishment)

    async def restore(self, accomplishment_id: uuid.UUID) -> Accomplishment | None:
        accomplishment = await self.repository.get(accomplishment_id)
        if accomplishment is None:
            return None

        accomplishment.archived_at = None
        return await self.repository.save(accomplishment)

    async def delete(self, accomplishment_id: uuid.UUID) -> bool:
        """Permanently remove an accomplishment. Returns False when it is missing."""
        accomplishment = await self.repository.get(accomplishment_id)
        if accomplishment is None:
            return False

        await self.repository.delete(accomplishment)
        return True
