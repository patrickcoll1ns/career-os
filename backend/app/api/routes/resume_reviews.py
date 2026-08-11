import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_database_session
from app.integrations.resume_reviewer import (
    AnthropicResumeReviewer,
    ResumeReviewGenerationError,
)
from app.repositories.documents import DocumentRepository
from app.repositories.resume_reviews import ResumeReviewRepository
from app.schemas.resume_review import ResumeReviewCreate, ResumeReviewRead
from app.services.resume_reviews import (
    ResumeDocumentNotFoundError,
    ResumeDocumentNotReadyError,
    ResumeReviewService,
)

router = APIRouter(prefix="/resume-reviews", tags=["resume reviews"])
DatabaseSession = Annotated[AsyncSession, Depends(get_database_session)]


def get_resume_review_service(session: DatabaseSession) -> ResumeReviewService:
    return ResumeReviewService(
        ResumeReviewRepository(session),
        DocumentRepository(session),
        AnthropicResumeReviewer(),
    )


ResumeReviewServiceDependency = Annotated[
    ResumeReviewService,
    Depends(get_resume_review_service),
]


@router.post("", response_model=ResumeReviewRead, status_code=status.HTTP_201_CREATED)
async def create_resume_review(
    review_data: ResumeReviewCreate,
    service: ResumeReviewServiceDependency,
) -> ResumeReviewRead:
    try:
        review = await service.create(
            review_data.document_id,
            review_data.target_role,
        )
    except ResumeDocumentNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
    except ResumeDocumentNotReadyError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(exc)
        ) from exc
    except ResumeReviewGenerationError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="The resume reviewer is unavailable right now.",
        ) from exc
    return ResumeReviewRead.model_validate(review)


@router.get("", response_model=list[ResumeReviewRead])
async def list_resume_reviews(
    service: ResumeReviewServiceDependency,
) -> list[ResumeReviewRead]:
    reviews = await service.list_all()
    return [ResumeReviewRead.model_validate(review) for review in reviews]


@router.get("/{review_id}", response_model=ResumeReviewRead)
async def get_resume_review(
    review_id: uuid.UUID,
    service: ResumeReviewServiceDependency,
) -> ResumeReviewRead:
    review = await service.get(review_id)
    if review is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume review not found.",
        )
    return ResumeReviewRead.model_validate(review)
