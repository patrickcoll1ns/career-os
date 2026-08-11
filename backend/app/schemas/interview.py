import uuid
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator


class InterviewType(str, Enum):
    BEHAVIORAL = "behavioral"
    TECHNICAL = "technical"
    MIXED = "mixed"


class InterviewDifficulty(str, Enum):
    INTRODUCTORY = "introductory"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class InterviewHighlight(BaseModel):
    title: str
    detail: str


class QuestionResult(BaseModel):
    """Claude's next interview question."""

    question: str


class TurnFeedback(BaseModel):
    """Claude's structured feedback on a single answer, stored on the turn."""

    score: int = Field(ge=1, le=5)
    strengths: str
    improvement: str


class SessionSummary(BaseModel):
    """Claude's aggregate feedback once an interview session is complete."""

    summary: str
    strengths: list[InterviewHighlight]
    improvements: list[InterviewHighlight]
    learning_recommendations: list[InterviewHighlight]


class InterviewSessionCreate(BaseModel):
    target_role: str = Field(min_length=1, max_length=200)
    interview_type: InterviewType
    difficulty: InterviewDifficulty
    question_limit: int = Field(default=5, ge=1, le=20)

    @field_validator("target_role")
    @classmethod
    def normalize_target_role(cls, value: str) -> str:
        target_role = value.strip()
        if not target_role:
            raise ValueError("Target role cannot be blank.")
        return target_role


class InterviewAnswerSubmit(BaseModel):
    answer: str = Field(min_length=1, max_length=8000)

    @field_validator("answer")
    @classmethod
    def normalize_answer(cls, value: str) -> str:
        answer = value.strip()
        if not answer:
            raise ValueError("Answer cannot be blank.")
        return answer


class InterviewTurnRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    sequence_number: int
    question: str
    answer: str | None
    feedback: TurnFeedback | dict = {}
    created_at: datetime
    updated_at: datetime


class InterviewSessionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    target_role: str
    interview_type: InterviewType
    difficulty: InterviewDifficulty
    question_limit: int
    status: str
    summary: str | None
    strengths: list[InterviewHighlight]
    improvements: list[InterviewHighlight]
    learning_recommendations: list[InterviewHighlight]
    error_message: str | None
    created_at: datetime
    updated_at: datetime


class InterviewSessionWithTurns(InterviewSessionRead):
    turns: list[InterviewTurnRead] = Field(default_factory=list)
