"""create interview sessions and turns

Revision ID: d9a2c7e45f10
Revises: a4d6e8f20b31
Create Date: 2026-08-10 23:59:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "d9a2c7e45f10"
down_revision: Union[str, Sequence[str], None] = "a4d6e8f20b31"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create persistent mock-interview sessions and ordered turns."""
    op.create_table(
        "interview_sessions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("target_role", sa.String(length=200), nullable=False),
        sa.Column("interview_type", sa.String(length=20), nullable=False),
        sa.Column("difficulty", sa.String(length=20), nullable=False),
        sa.Column(
            "question_limit",
            sa.SmallInteger(),
            server_default="5",
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.String(length=20),
            server_default="active",
            nullable=False,
        ),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column(
            "strengths",
            sa.JSON(),
            server_default=sa.text("'[]'::json"),
            nullable=False,
        ),
        sa.Column(
            "improvements",
            sa.JSON(),
            server_default=sa.text("'[]'::json"),
            nullable=False,
        ),
        sa.Column(
            "learning_recommendations",
            sa.JSON(),
            server_default=sa.text("'[]'::json"),
            nullable=False,
        ),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "interview_type IN ('behavioral', 'technical', 'mixed')",
            name="ck_interview_sessions_type",
        ),
        sa.CheckConstraint(
            "difficulty IN ('introductory', 'intermediate', 'advanced')",
            name="ck_interview_sessions_difficulty",
        ),
        sa.CheckConstraint(
            "status IN ('active', 'completed', 'abandoned')",
            name="ck_interview_sessions_status",
        ),
        sa.CheckConstraint(
            "question_limit BETWEEN 1 AND 20",
            name="ck_interview_sessions_question_limit",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "interview_turns",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("session_id", sa.Uuid(), nullable=False),
        sa.Column("sequence_number", sa.SmallInteger(), nullable=False),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("answer", sa.Text(), nullable=True),
        sa.Column(
            "feedback",
            sa.JSON(),
            server_default=sa.text("'{}'::json"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "sequence_number >= 1",
            name="ck_interview_turns_sequence_number",
        ),
        sa.ForeignKeyConstraint(
            ["session_id"],
            ["interview_sessions.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "session_id",
            "sequence_number",
            name="uq_interview_turns_session_sequence",
        ),
    )
    op.create_index(
        op.f("ix_interview_turns_session_id"),
        "interview_turns",
        ["session_id"],
    )


def downgrade() -> None:
    """Remove mock-interview persistence."""
    op.drop_index(
        op.f("ix_interview_turns_session_id"),
        table_name="interview_turns",
    )
    op.drop_table("interview_turns")
    op.drop_table("interview_sessions")
