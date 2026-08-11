import uuid
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock

from fastapi.testclient import TestClient

from app.api.routes.resume_reviews import get_resume_review_service
from app.integrations.resume_reviewer import ResumeReviewGenerationError
from app.main import app
from app.services.resume_reviews import (
    ResumeDocumentNotFoundError,
    ResumeDocumentNotReadyError,
    ResumeReviewService,
)

client = TestClient(app)


def review_record(**overrides):
    timestamp = datetime(2026, 8, 10, tzinfo=UTC)
    values = {
        "id": uuid.uuid4(),
        "document_id": uuid.uuid4(),
        "target_role": "Backend engineer",
        "status": "completed",
        "summary": "Strong foundation.",
        "strengths": [],
        "gaps": [],
        "rewrite_suggestions": [],
        "error_message": None,
        "created_at": timestamp,
        "updated_at": timestamp,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def test_create_resume_review() -> None:
    document_id = uuid.uuid4()
    service = AsyncMock(spec=ResumeReviewService)
    service.create.return_value = review_record(document_id=document_id)
    app.dependency_overrides[get_resume_review_service] = lambda: service

    try:
        response = client.post(
            "/resume-reviews",
            json={"document_id": str(document_id), "target_role": "Backend engineer"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 201
    assert response.json()["status"] == "completed"
    service.create.assert_awaited_once_with(document_id, "Backend engineer")


def test_list_resume_reviews() -> None:
    service = AsyncMock(spec=ResumeReviewService)
    service.list_all.return_value = [review_record()]
    app.dependency_overrides[get_resume_review_service] = lambda: service

    try:
        response = client.get("/resume-reviews")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert len(response.json()) == 1


def test_get_resume_review_returns_not_found() -> None:
    service = AsyncMock(spec=ResumeReviewService)
    service.get.return_value = None
    app.dependency_overrides[get_resume_review_service] = lambda: service

    try:
        response = client.get(f"/resume-reviews/{uuid.uuid4()}")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404


def test_create_maps_document_errors() -> None:
    document_id = uuid.uuid4()
    cases = [
        (ResumeDocumentNotFoundError("missing"), 404),
        (ResumeDocumentNotReadyError("not ready"), 409),
        (ResumeReviewGenerationError("failed"), 502),
    ]

    for error, expected_status in cases:
        service = AsyncMock(spec=ResumeReviewService)
        service.create.side_effect = error
        app.dependency_overrides[get_resume_review_service] = lambda service=service: (
            service
        )
        try:
            response = client.post(
                "/resume-reviews",
                json={"document_id": str(document_id)},
            )
        finally:
            app.dependency_overrides.clear()
        assert response.status_code == expected_status
