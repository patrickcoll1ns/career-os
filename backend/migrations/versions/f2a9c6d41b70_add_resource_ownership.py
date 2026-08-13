"""add resource ownership

Revision ID: f2a9c6d41b70
Revises: e1f4a7c93b25
Create Date: 2026-08-13
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "f2a9c6d41b70"
down_revision: str | None = "e1f4a7c93b25"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

OWNED_TABLES = (
    "goals",
    "accomplishments",
    "conversations",
    "documents",
    "resume_reviews",
    "interview_sessions",
)


def upgrade() -> None:
    for table in OWNED_TABLES:
        op.add_column(
            table,
            sa.Column(
                "owner_id",
                sa.String(length=200),
                nullable=False,
                server_default="development:local",
            ),
        )
        op.create_index(f"ix_{table}_owner_id", table, ["owner_id"])
        op.alter_column(table, "owner_id", server_default=None)


def downgrade() -> None:
    for table in reversed(OWNED_TABLES):
        op.drop_index(f"ix_{table}_owner_id", table_name=table)
        op.drop_column(table, "owner_id")
