import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.rate_limit import rate_limit
from app.db.session import get_database_session
from app.integrations.interviewer import AnthropicInterviewer, InterviewGenerationError
from app.models.interview import InterviewSession, InterviewTurn
from app.repositories.interviews import InterviewRepository
from app.schemas.interview import (
    InterviewAnswerSubmit,
    InterviewSessionCreate,
    InterviewSessionRead,
    InterviewSessionWithTurns,
    InterviewTurnRead,
)
from app.services.interviews import (
    InterviewNoOpenQuestionError,
    InterviewService,
    InterviewSessionNotActiveError,
    InterviewSessionNotFoundError,
)

router = APIRouter(prefix="/interviews", tags=["interviews"])
DatabaseSession = Annotated[AsyncSession, Depends(get_database_session)]


def get_interview_service(session: DatabaseSession) -> InterviewService:
    return InterviewService(
        InterviewRepository(session),
        AnthropicInterviewer(),
    )


InterviewServiceDependency = Annotated[InterviewService, Depends(get_interview_service)]


def _to_session_with_turns(
    interview_session: InterviewSession, turns: list[InterviewTurn]
) -> InterviewSessionWithTurns:
    return InterviewSessionWithTurns(
        **InterviewSessionRead.model_validate(interview_session).model_dump(),
        turns=[InterviewTurnRead.model_validate(turn) for turn in turns],
    )


@router.post(
    "",
    response_model=InterviewSessionWithTurns,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(rate_limit("ai", "rate_limit_ai_requests"))],
)
async def create_interview_session(
    session_data: InterviewSessionCreate,
    service: InterviewServiceDependency,
) -> InterviewSessionWithTurns:
    try:
        interview_session, turns = await service.create_session(
            session_data.target_role,
            session_data.interview_type.value,
            session_data.difficulty.value,
            session_data.question_limit,
        )
    except InterviewGenerationError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="The mock interviewer is unavailable right now.",
        ) from exc
    return _to_session_with_turns(interview_session, turns)


@router.get("", response_model=list[InterviewSessionRead])
async def list_interview_sessions(
    service: InterviewServiceDependency,
) -> list[InterviewSessionRead]:
    sessions = await service.list_sessions()
    return [InterviewSessionRead.model_validate(session) for session in sessions]


@router.get("/{session_id}", response_model=InterviewSessionWithTurns)
async def get_interview_session(
    session_id: uuid.UUID,
    service: InterviewServiceDependency,
) -> InterviewSessionWithTurns:
    result = await service.get_session_with_turns(session_id)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Interview session not found.",
        )
    return _to_session_with_turns(*result)


@router.post(
    "/{session_id}/answers",
    response_model=InterviewSessionWithTurns,
    dependencies=[Depends(rate_limit("ai", "rate_limit_ai_requests"))],
)
async def submit_interview_answer(
    session_id: uuid.UUID,
    answer_data: InterviewAnswerSubmit,
    service: InterviewServiceDependency,
) -> InterviewSessionWithTurns:
    try:
        interview_session, turns = await service.submit_answer(
            session_id, answer_data.answer
        )
    except InterviewSessionNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
    except (InterviewSessionNotActiveError, InterviewNoOpenQuestionError) as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(exc)
        ) from exc
    except InterviewGenerationError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="The mock interviewer is unavailable right now.",
        ) from exc
    return _to_session_with_turns(interview_session, turns)
