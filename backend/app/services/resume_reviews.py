import uuid

from app.integrations.resume_reviewer import (
    AnthropicResumeReviewer,
    ResumeReviewGenerationError,
)
from app.models.resume_review import ResumeReview
from app.repositories.documents import DocumentRepository
from app.repositories.resume_reviews import ResumeReviewRepository


class ResumeDocumentNotFoundError(LookupError):
    """Raised when a requested source document does not exist."""


class ResumeDocumentNotReadyError(RuntimeError):
    """Raised when a source document has not been indexed successfully."""


class ResumeReviewService:
    """Coordinate source documents, Claude review, and persisted results."""

    def __init__(
        self,
        repository: ResumeReviewRepository,
        document_repository: DocumentRepository,
        reviewer: AnthropicResumeReviewer,
    ) -> None:
        self.repository = repository
        self.document_repository = document_repository
        self.reviewer = reviewer

    async def create(
        self, document_id: uuid.UUID, target_role: str | None
    ) -> ResumeReview:
        document = await self.document_repository.get(document_id)
        if document is None:
            raise ResumeDocumentNotFoundError("Resume document not found.")
        if document.status != "ready" or not document.extracted_text:
            raise ResumeDocumentNotReadyError(
                "The document must be indexed successfully before review."
            )

        review = await self.repository.add(
            ResumeReview(
                document_id=document.id,
                target_role=target_role,
                status="pending",
            )
        )

        try:
            result = await self.reviewer.review(
                document.extracted_text,
                document.original_filename,
                target_role,
            )
        except ResumeReviewGenerationError:
            review.status = "failed"
            review.error_message = "Claude could not generate the resume review."
            await self.repository.update(review)
            raise

        review.status = "completed"
        review.summary = result.summary
        review.strengths = [item.model_dump() for item in result.strengths]
        review.gaps = [item.model_dump() for item in result.gaps]
        review.rewrite_suggestions = [
            suggestion.model_dump() for suggestion in result.rewrite_suggestions
        ]
        review.error_message = None
        return await self.repository.update(review)

    async def get(self, review_id: uuid.UUID) -> ResumeReview | None:
        return await self.repository.get(review_id)

    async def list_all(self) -> list[ResumeReview]:
        return await self.repository.list_all()
