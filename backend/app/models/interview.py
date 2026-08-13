import uuid
from datetime import datetime

from sqlalchemy import (
    JSON,
    CheckConstraint,
    DateTime,
    ForeignKey,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class InterviewSession(Base):
    """Configuration and aggregate feedback for one mock interview."""

    __tablename__ = "interview_sessions"
    __table_args__ = (
        CheckConstraint(
            "interview_type IN ('behavioral', 'technical', 'mixed')",
            name="ck_interview_sessions_type",
        ),
        CheckConstraint(
            "difficulty IN ('introductory', 'intermediate', 'advanced')",
            name="ck_interview_sessions_difficulty",
        ),
        CheckConstraint(
            "status IN ('active', 'completed', 'abandoned')",
            name="ck_interview_sessions_status",
        ),
        CheckConstraint(
            "question_limit BETWEEN 1 AND 20",
            name="ck_interview_sessions_question_limit",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
    )
    owner_id: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    target_role: Mapped[str] = mapped_column(String(200), nullable=False)
    interview_type: Mapped[str] = mapped_column(String(20), nullable=False)
    difficulty: Mapped[str] = mapped_column(String(20), nullable=False)
    question_limit: Mapped[int] = mapped_column(
        SmallInteger,
        nullable=False,
        default=5,
        server_default="5",
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="active",
        server_default="active",
    )
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    strengths: Mapped[list[dict[str, str]]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
    )
    improvements: Mapped[list[dict[str, str]]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
    )
    learning_recommendations: Mapped[list[dict[str, str]]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


class InterviewTurn(Base):
    """One ordered interview question, answer, and structured feedback."""

    __tablename__ = "interview_turns"
    __table_args__ = (
        UniqueConstraint(
            "session_id",
            "sequence_number",
            name="uq_interview_turns_session_sequence",
        ),
        CheckConstraint(
            "sequence_number >= 1",
            name="ck_interview_turns_sequence_number",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("interview_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    sequence_number: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    answer: Mapped[str | None] = mapped_column(Text, nullable=True)
    feedback: Mapped[dict[str, str | int]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
