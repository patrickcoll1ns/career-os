import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.resume_review import ResumeReview


class ResumeReviewRepository:
    """Persist and retrieve structured resume reviews."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add(self, review: ResumeReview) -> ResumeReview:
        return await self._save(review)

    async def update(self, review: ResumeReview) -> ResumeReview:
        return await self._save(review)

    async def _save(self, review: ResumeReview) -> ResumeReview:
        self.session.add(review)
        try:
            await self.session.commit()
        except Exception:
            await self.session.rollback()
            raise
        await self.session.refresh(review)
        return review

    async def get(self, review_id: uuid.UUID) -> ResumeReview | None:
        return await self.session.get(ResumeReview, review_id)

    async def list_all(self) -> list[ResumeReview]:
        result = await self.session.scalars(
            select(ResumeReview).order_by(ResumeReview.created_at.desc())
        )
        return list(result.all())
