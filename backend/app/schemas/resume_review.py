import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ReviewFinding(BaseModel):
    title: str
    evidence: str
    recommendation: str


class RewriteSuggestion(BaseModel):
    original: str
    rewrite: str
    rationale: str


class ResumeReviewResult(BaseModel):
    summary: str
    strengths: list[ReviewFinding]
    gaps: list[ReviewFinding]
    rewrite_suggestions: list[RewriteSuggestion]


class ResumeReviewCreate(BaseModel):
    document_id: uuid.UUID
    target_role: str | None = Field(default=None, max_length=200)

    @field_validator("target_role")
    @classmethod
    def normalize_target_role(cls, value: str | None) -> str | None:
        if value is None:
            return None
        target_role = value.strip()
        return target_role or None


class ResumeReviewRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    document_id: uuid.UUID
    target_role: str | None
    status: str
    summary: str | None
    strengths: list[ReviewFinding]
    gaps: list[ReviewFinding]
    rewrite_suggestions: list[RewriteSuggestion]
    error_message: str | None
    created_at: datetime
    updated_at: datetime
