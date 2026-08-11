import asyncio
import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.integrations.resume_reviewer import (
    AnthropicResumeReviewer,
    ResumeReviewGenerationError,
)
from app.repositories.documents import DocumentRepository
from app.repositories.resume_reviews import ResumeReviewRepository
from app.schemas.resume_review import (
    ResumeReviewResult,
    ReviewFinding,
    RewriteSuggestion,
)
from app.services.resume_reviews import (
    ResumeDocumentNotFoundError,
    ResumeDocumentNotReadyError,
    ResumeReviewService,
)


def make_service():
    repository = AsyncMock(spec=ResumeReviewRepository)
    repository.add.side_effect = lambda review: review
    repository.update.side_effect = lambda review: review
    document_repository = AsyncMock(spec=DocumentRepository)
    reviewer = AsyncMock(spec=AnthropicResumeReviewer)
    service = ResumeReviewService(repository, document_repository, reviewer)
    return service, repository, document_repository, reviewer


def ready_document():
    return SimpleNamespace(
        id=uuid.uuid4(),
        status="ready",
        extracted_text="Built FastAPI services and PostgreSQL data models.",
        original_filename="resume.pdf",
    )


def review_result() -> ResumeReviewResult:
    return ResumeReviewResult(
        summary="Strong technical foundation with room for more quantified impact.",
        strengths=[
            ReviewFinding(
                title="Relevant backend stack",
                evidence="FastAPI and PostgreSQL are named.",
                recommendation="Keep this technical specificity.",
            )
        ],
        gaps=[
            ReviewFinding(
                title="Impact is unquantified",
                evidence="The bullet contains no outcome metric.",
                recommendation="Add a verified impact measure if available.",
            )
        ],
        rewrite_suggestions=[
            RewriteSuggestion(
                original="Built FastAPI services.",
                rewrite="Built FastAPI services backed by PostgreSQL.",
                rationale="Names the persistence layer without inventing impact.",
            )
        ],
    )


def test_create_persists_structured_completed_review() -> None:
    service, repository, document_repository, reviewer = make_service()
    document = ready_document()
    document_repository.get.return_value = document
    reviewer.review.return_value = review_result()

    review = asyncio.run(service.create(document.id, "Backend engineer"))

    assert review.status == "completed"
    assert review.summary == review_result().summary
    assert review.strengths[0]["title"] == "Relevant backend stack"
    assert review.gaps[0]["title"] == "Impact is unquantified"
    assert review.rewrite_suggestions[0]["rewrite"].startswith("Built FastAPI")
    reviewer.review.assert_awaited_once_with(
        document.extracted_text,
        "resume.pdf",
        "Backend engineer",
    )
    assert repository.update.await_count == 1


def test_create_rejects_missing_document_before_review() -> None:
    service, repository, document_repository, reviewer = make_service()
    document_repository.get.return_value = None

    with pytest.raises(ResumeDocumentNotFoundError):
        asyncio.run(service.create(uuid.uuid4(), None))

    repository.add.assert_not_awaited()
    reviewer.review.assert_not_awaited()


@pytest.mark.parametrize(
    "document",
    [
        SimpleNamespace(status="processing", extracted_text=None),
        SimpleNamespace(status="ready", extracted_text=None),
    ],
)
def test_create_rejects_document_that_is_not_ready(document) -> None:
    service, repository, document_repository, reviewer = make_service()
    document_repository.get.return_value = document

    with pytest.raises(ResumeDocumentNotReadyError):
        asyncio.run(service.create(uuid.uuid4(), None))

    repository.add.assert_not_awaited()
    reviewer.review.assert_not_awaited()


def test_generation_failure_is_persisted_before_error_is_reraised() -> None:
    service, repository, document_repository, reviewer = make_service()
    document = ready_document()
    document_repository.get.return_value = document
    reviewer.review.side_effect = ResumeReviewGenerationError("API unavailable")

    with pytest.raises(ResumeReviewGenerationError):
        asyncio.run(service.create(document.id, None))

    failed_review = repository.update.await_args.args[0]
    assert failed_review.status == "failed"
    assert failed_review.error_message == "Claude could not generate the resume review."
