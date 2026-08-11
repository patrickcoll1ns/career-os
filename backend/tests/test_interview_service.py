import asyncio
import uuid
from unittest.mock import AsyncMock

import pytest

from app.integrations.interviewer import AnthropicInterviewer, InterviewGenerationError
from app.models.interview import InterviewSession, InterviewTurn
from app.repositories.interviews import InterviewRepository
from app.schemas.interview import (
    InterviewHighlight,
    QuestionResult,
    SessionSummary,
    TurnFeedback,
)
from app.services.interviews import (
    InterviewNoOpenQuestionError,
    InterviewService,
    InterviewSessionNotActiveError,
    InterviewSessionNotFoundError,
)


def make_service():
    repository = AsyncMock(spec=InterviewRepository)
    repository.add_session.side_effect = lambda session: session
    repository.update_session.side_effect = lambda session: session
    repository.add_turn.side_effect = lambda turn: turn
    repository.update_turn.side_effect = lambda turn: turn
    interviewer = AsyncMock(spec=AnthropicInterviewer)
    service = InterviewService(repository, interviewer)
    return service, repository, interviewer


def active_session(**overrides) -> InterviewSession:
    values = {
        "id": uuid.uuid4(),
        "target_role": "Backend engineer",
        "interview_type": "behavioral",
        "difficulty": "intermediate",
        "question_limit": 2,
        "status": "active",
    }
    values.update(overrides)
    return InterviewSession(**values)


def turn(
    sequence_number: int, question: str, answer: str | None = None
) -> InterviewTurn:
    return InterviewTurn(
        id=uuid.uuid4(),
        session_id=uuid.uuid4(),
        sequence_number=sequence_number,
        question=question,
        answer=answer,
        feedback={},
    )


def test_create_session_persists_active_session_with_first_turn() -> None:
    service, repository, interviewer = make_service()
    interviewer.generate_question.return_value = QuestionResult(
        question="Tell me about a challenging project."
    )

    session, turns = asyncio.run(
        service.create_session("Backend engineer", "behavioral", "intermediate", 3)
    )

    assert session.status == "active"
    assert len(turns) == 1
    assert turns[0].sequence_number == 1
    assert turns[0].question == "Tell me about a challenging project."
    interviewer.generate_question.assert_awaited_once_with(
        "Backend engineer", "behavioral", "intermediate", []
    )
    repository.update_session.assert_not_awaited()


def test_create_session_marks_abandoned_on_generation_failure() -> None:
    service, repository, interviewer = make_service()
    interviewer.generate_question.side_effect = InterviewGenerationError("down")

    with pytest.raises(InterviewGenerationError):
        asyncio.run(
            service.create_session("Backend engineer", "behavioral", "intermediate", 3)
        )

    abandoned_session = repository.update_session.await_args.args[0]
    assert abandoned_session.status == "abandoned"
    assert abandoned_session.error_message is not None
    repository.add_turn.assert_not_awaited()


def test_submit_answer_records_feedback_and_asks_next_question() -> None:
    service, repository, interviewer = make_service()
    session = active_session(question_limit=2)
    first_turn = turn(1, "Describe a bug you fixed.")
    repository.get_session.return_value = session
    repository.list_turns.return_value = [first_turn]
    interviewer.evaluate_answer.return_value = TurnFeedback(
        score=4, strengths="Specific example.", improvement="Add measurable impact."
    )
    interviewer.generate_question.return_value = QuestionResult(
        question="Tell me about a disagreement with a teammate."
    )

    updated_session, turns = asyncio.run(
        service.submit_answer(session.id, "I fixed a race condition in the queue.")
    )

    assert updated_session.status == "active"
    assert first_turn.answer == "I fixed a race condition in the queue."
    assert first_turn.feedback["score"] == 4
    assert len(turns) == 2
    assert turns[1].sequence_number == 2
    interviewer.generate_summary.assert_not_awaited()


def test_submit_answer_completes_session_and_persists_summary() -> None:
    service, repository, interviewer = make_service()
    session = active_session(question_limit=1)
    only_turn = turn(1, "Describe a bug you fixed.")
    repository.get_session.return_value = session
    repository.list_turns.return_value = [only_turn]
    interviewer.evaluate_answer.return_value = TurnFeedback(
        score=5, strengths="Great detail.", improvement="None needed."
    )
    interviewer.generate_summary.return_value = SessionSummary(
        summary="Strong technical communicator.",
        strengths=[
            InterviewHighlight(title="Debugging", detail="Clear root-cause story.")
        ],
        improvements=[
            InterviewHighlight(title="Metrics", detail="Quantify outcomes more.")
        ],
        learning_recommendations=[
            InterviewHighlight(title="Practice", detail="Rehearse quantified answers.")
        ],
    )

    updated_session, turns = asyncio.run(
        service.submit_answer(session.id, "I fixed a race condition in the queue.")
    )

    assert updated_session.status == "completed"
    assert updated_session.summary == "Strong technical communicator."
    assert updated_session.strengths[0]["title"] == "Debugging"
    assert len(turns) == 1
    interviewer.generate_question.assert_not_awaited()


def test_submit_answer_rejects_missing_session() -> None:
    service, repository, interviewer = make_service()
    repository.get_session.return_value = None

    with pytest.raises(InterviewSessionNotFoundError):
        asyncio.run(service.submit_answer(uuid.uuid4(), "answer"))

    interviewer.evaluate_answer.assert_not_awaited()


def test_submit_answer_rejects_inactive_session() -> None:
    service, repository, interviewer = make_service()
    repository.get_session.return_value = active_session(status="completed")

    with pytest.raises(InterviewSessionNotActiveError):
        asyncio.run(service.submit_answer(uuid.uuid4(), "answer"))

    interviewer.evaluate_answer.assert_not_awaited()


def test_submit_answer_rejects_when_no_open_question() -> None:
    service, repository, interviewer = make_service()
    session = active_session(question_limit=1)
    repository.get_session.return_value = session
    repository.list_turns.return_value = [
        turn(1, "Question", answer="Already answered")
    ]

    with pytest.raises(InterviewNoOpenQuestionError):
        asyncio.run(service.submit_answer(session.id, "answer"))

    interviewer.evaluate_answer.assert_not_awaited()


def test_submit_answer_marks_abandoned_when_next_question_generation_fails() -> None:
    service, repository, interviewer = make_service()
    session = active_session(question_limit=2)
    first_turn = turn(1, "Describe a bug you fixed.")
    repository.get_session.return_value = session
    repository.list_turns.return_value = [first_turn]
    interviewer.evaluate_answer.return_value = TurnFeedback(
        score=3, strengths="Ok.", improvement="More depth."
    )
    interviewer.generate_question.side_effect = InterviewGenerationError("down")

    with pytest.raises(InterviewGenerationError):
        asyncio.run(service.submit_answer(session.id, "answer"))

    abandoned_session = repository.update_session.await_args.args[0]
    assert abandoned_session.status == "abandoned"


def test_submit_answer_marks_abandoned_when_summary_generation_fails() -> None:
    service, repository, interviewer = make_service()
    session = active_session(question_limit=1)
    only_turn = turn(1, "Describe a bug you fixed.")
    repository.get_session.return_value = session
    repository.list_turns.return_value = [only_turn]
    interviewer.evaluate_answer.return_value = TurnFeedback(
        score=3, strengths="Ok.", improvement="More depth."
    )
    interviewer.generate_summary.side_effect = InterviewGenerationError("down")

    with pytest.raises(InterviewGenerationError):
        asyncio.run(service.submit_answer(session.id, "answer"))

    abandoned_session = repository.update_session.await_args.args[0]
    assert abandoned_session.status == "abandoned"
