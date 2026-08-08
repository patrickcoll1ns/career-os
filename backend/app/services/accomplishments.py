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

    async def list_all(self) -> list[Accomplishment]:
        return await self.repository.list_all()
