import uuid
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock

from fastapi.testclient import TestClient

from app.api.routes.interviews import get_interview_service
from app.integrations.interviewer import InterviewGenerationError
from app.main import app
from app.services.interviews import (
    InterviewNoOpenQuestionError,
    InterviewService,
    InterviewSessionNotActiveError,
    InterviewSessionNotFoundError,
)

client = TestClient(app)


def session_record(**overrides):
    timestamp = datetime(2026, 8, 10, tzinfo=UTC)
    values = {
        "id": uuid.uuid4(),
        "target_role": "Backend engineer",
        "interview_type": "behavioral",
        "difficulty": "intermediate",
        "question_limit": 3,
        "status": "active",
        "summary": None,
        "strengths": [],
        "improvements": [],
        "learning_recommendations": [],
        "error_message": None,
        "created_at": timestamp,
        "updated_at": timestamp,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def turn_record(**overrides):
    timestamp = datetime(2026, 8, 10, tzinfo=UTC)
    values = {
        "id": uuid.uuid4(),
        "sequence_number": 1,
        "question": "Tell me about a challenging project.",
        "answer": None,
        "feedback": {},
        "created_at": timestamp,
        "updated_at": timestamp,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def test_create_interview_session() -> None:
    service = AsyncMock(spec=InterviewService)
    service.create_session.return_value = (session_record(), [turn_record()])
    app.dependency_overrides[get_interview_service] = lambda: service

    try:
        response = client.post(
            "/interviews",
            json={
                "target_role": "Backend engineer",
                "interview_type": "behavioral",
                "difficulty": "intermediate",
                "question_limit": 3,
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "active"
    assert len(body["turns"]) == 1
    service.create_session.assert_awaited_once_with(
        "Backend engineer", "behavioral", "intermediate", 3
    )


def test_create_interview_session_maps_generation_error() -> None:
    service = AsyncMock(spec=InterviewService)
    service.create_session.side_effect = InterviewGenerationError("down")
    app.dependency_overrides[get_interview_service] = lambda: service

    try:
        response = client.post(
            "/interviews",
            json={
                "target_role": "Backend engineer",
                "interview_type": "behavioral",
                "difficulty": "intermediate",
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 502


def test_list_interview_sessions() -> None:
    service = AsyncMock(spec=InterviewService)
    service.list_sessions.return_value = [session_record()]
    app.dependency_overrides[get_interview_service] = lambda: service

    try:
        response = client.get("/interviews")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert len(response.json()) == 1


def test_get_interview_session_returns_not_found() -> None:
    service = AsyncMock(spec=InterviewService)
    service.get_session_with_turns.return_value = None
    app.dependency_overrides[get_interview_service] = lambda: service

    try:
        response = client.get(f"/interviews/{uuid.uuid4()}")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404


def test_get_interview_session_returns_session_with_turns() -> None:
    service = AsyncMock(spec=InterviewService)
    service.get_session_with_turns.return_value = (session_record(), [turn_record()])
    app.dependency_overrides[get_interview_service] = lambda: service

    try:
        response = client.get(f"/interviews/{uuid.uuid4()}")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert len(response.json()["turns"]) == 1


def test_submit_interview_answer() -> None:
    service = AsyncMock(spec=InterviewService)
    answered_turn = turn_record(
        answer="I fixed a race condition.",
        feedback={"score": 4, "strengths": "Specific.", "improvement": "Add metrics."},
    )
    next_turn = turn_record(sequence_number=2, question="Next question.")
    service.submit_answer.return_value = (session_record(), [answered_turn, next_turn])
    app.dependency_overrides[get_interview_service] = lambda: service

    try:
        response = client.post(
            f"/interviews/{uuid.uuid4()}/answers",
            json={"answer": "I fixed a race condition."},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert len(body["turns"]) == 2
    assert body["turns"][0]["feedback"]["score"] == 4


def test_submit_interview_answer_maps_errors() -> None:
    cases = [
        (InterviewSessionNotFoundError("missing"), 404),
        (InterviewSessionNotActiveError("ended"), 409),
        (InterviewNoOpenQuestionError("no open question"), 409),
        (InterviewGenerationError("down"), 502),
    ]

    for error, expected_status in cases:
        service = AsyncMock(spec=InterviewService)
        service.submit_answer.side_effect = error
        app.dependency_overrides[get_interview_service] = lambda service=service: (
            service
        )
        try:
            response = client.post(
                f"/interviews/{uuid.uuid4()}/answers",
                json={"answer": "An answer."},
            )
        finally:
            app.dependency_overrides.clear()
        assert response.status_code == expected_status
