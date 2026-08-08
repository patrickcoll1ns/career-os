"""add archived_at to goals

Revision ID: 13cc806bed87
Revises: 917656c03469
Create Date: 2026-08-08 11:29:09.117625
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "13cc806bed87"
down_revision: Union[str, Sequence[str], None] = "917656c03469"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add a nullable archived_at column used for soft-deleting goals."""
    op.add_column(
        "goals",
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    """Remove the archived_at column."""
    op.drop_column("goals", "archived_at")
