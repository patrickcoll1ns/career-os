import uuid

from app.integrations.interviewer import AnthropicInterviewer, InterviewGenerationError
from app.models.interview import InterviewSession, InterviewTurn
from app.repositories.interviews import InterviewRepository

SessionWithTurns = tuple[InterviewSession, list[InterviewTurn]]


class InterviewSessionNotFoundError(LookupError):
    """Raised when a requested interview session does not exist."""


class InterviewSessionNotActiveError(RuntimeError):
    """Raised when an answer is submitted to a finished interview session."""


class InterviewNoOpenQuestionError(RuntimeError):
    """Raised when a session has no unanswered question to respond to."""


class InterviewService:
    """Coordinate Claude-driven question generation, scoring, and summaries."""

    def __init__(
        self,
        repository: InterviewRepository,
        interviewer: AnthropicInterviewer,
    ) -> None:
        self.repository = repository
        self.interviewer = interviewer

    async def create_session(
        self,
        target_role: str,
        interview_type: str,
        difficulty: str,
        question_limit: int,
    ) -> SessionWithTurns:
        session = await self.repository.add_session(
            InterviewSession(
                target_role=target_role,
                interview_type=interview_type,
                difficulty=difficulty,
                question_limit=question_limit,
                status="active",
            )
        )

        try:
            question_result = await self.interviewer.generate_question(
                target_role, interview_type, difficulty, []
            )
        except InterviewGenerationError:
            session.status = "abandoned"
            session.error_message = (
                "Claude could not generate the first interview question."
            )
            await self.repository.update_session(session)
            raise

        first_turn = await self.repository.add_turn(
            InterviewTurn(
                session_id=session.id,
                sequence_number=1,
                question=question_result.question,
            )
        )
        return session, [first_turn]

    async def get_session_with_turns(
        self, session_id: uuid.UUID
    ) -> SessionWithTurns | None:
        session = await self.repository.get_session(session_id)
        if session is None:
            return None
        turns = await self.repository.list_turns(session_id)
        return session, turns

    async def list_sessions(self) -> list[InterviewSession]:
        return await self.repository.list_sessions()

    async def submit_answer(
        self, session_id: uuid.UUID, answer: str
    ) -> SessionWithTurns:
        session = await self.repository.get_session(session_id)
        if session is None:
            raise InterviewSessionNotFoundError("Interview session not found.")
        if session.status != "active":
            raise InterviewSessionNotActiveError(
                "This interview session has already ended."
            )

        turns = await self.repository.list_turns(session_id)
        open_turn = next(
            (turn for turn in reversed(turns) if turn.answer is None), None
        )
        if open_turn is None:
            raise InterviewNoOpenQuestionError("There is no open question to answer.")

        feedback = await self.interviewer.evaluate_answer(
            session.target_role, open_turn.question, answer
        )
        open_turn.answer = answer
        open_turn.feedback = feedback.model_dump()
        await self.repository.update_turn(open_turn)

        if len(turns) < session.question_limit:
            await self._ask_next_question(session, turns)
        else:
            await self._complete_session(session, turns)

        return session, turns

    async def _ask_next_question(
        self, session: InterviewSession, turns: list[InterviewTurn]
    ) -> None:
        try:
            question_result = await self.interviewer.generate_question(
                session.target_role,
                session.interview_type,
                session.difficulty,
                [(turn.question, turn.answer) for turn in turns],
            )
        except InterviewGenerationError:
            session.status = "abandoned"
            session.error_message = (
                "Claude could not generate the next interview question."
            )
            await self.repository.update_session(session)
            raise

        next_turn = await self.repository.add_turn(
            InterviewTurn(
                session_id=session.id,
                sequence_number=len(turns) + 1,
                question=question_result.question,
            )
        )
        turns.append(next_turn)

    async def _complete_session(
        self, session: InterviewSession, turns: list[InterviewTurn]
    ) -> None:
        try:
            summary = await self.interviewer.generate_summary(
                session.target_role,
                [(turn.question, turn.answer) for turn in turns],
            )
        except InterviewGenerationError:
            session.status = "abandoned"
            session.error_message = "Claude could not generate the interview summary."
            await self.repository.update_session(session)
            raise

        session.status = "completed"
        session.summary = summary.summary
        session.strengths = [item.model_dump() for item in summary.strengths]
        session.improvements = [item.model_dump() for item in summary.improvements]
        session.learning_recommendations = [
            item.model_dump() for item in summary.learning_recommendations
        ]
        session.error_message = None
        await self.repository.update_session(session)
