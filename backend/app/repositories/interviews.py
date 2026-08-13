import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_owner_id
from app.models.interview import InterviewSession, InterviewTurn


class InterviewRepository:
    """Persist and retrieve mock interview sessions and turns."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.owner_id = get_current_owner_id()

    async def add_session(
        self, interview_session: InterviewSession
    ) -> InterviewSession:
        interview_session.owner_id = self.owner_id
        return await self._save(interview_session)

    async def update_session(
        self, interview_session: InterviewSession
    ) -> InterviewSession:
        return await self._save(interview_session)

    async def _save(self, interview_session: InterviewSession) -> InterviewSession:
        self.session.add(interview_session)
        try:
            await self.session.commit()
        except Exception:
            await self.session.rollback()
            raise
        await self.session.refresh(interview_session)
        return interview_session

    async def get_session(self, session_id: uuid.UUID) -> InterviewSession | None:
        return await self.session.scalar(
            select(InterviewSession).where(
                InterviewSession.id == session_id,
                InterviewSession.owner_id == self.owner_id,
            )
        )

    async def list_sessions(self) -> list[InterviewSession]:
        result = await self.session.scalars(
            select(InterviewSession)
            .order_by(InterviewSession.created_at.desc())
            .where(InterviewSession.owner_id == self.owner_id)
        )
        return list(result.all())

    async def add_turn(self, turn: InterviewTurn) -> InterviewTurn:
        self.session.add(turn)
        try:
            await self.session.commit()
        except Exception:
            await self.session.rollback()
            raise
        await self.session.refresh(turn)
        return turn

    async def update_turn(self, turn: InterviewTurn) -> InterviewTurn:
        return await self.add_turn(turn)

    async def list_turns(self, session_id: uuid.UUID) -> list[InterviewTurn]:
        result = await self.session.scalars(
            select(InterviewTurn)
            .join(InterviewSession, InterviewSession.id == InterviewTurn.session_id)
            .where(
                InterviewTurn.session_id == session_id,
                InterviewSession.owner_id == self.owner_id,
            )
            .order_by(InterviewTurn.sequence_number.asc())
        )
        return list(result.all())
