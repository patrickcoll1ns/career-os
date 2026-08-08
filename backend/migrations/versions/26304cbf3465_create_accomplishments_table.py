"""create accomplishments table

Revision ID: 26304cbf3465
Revises: 13cc806bed87
Create Date: 2026-08-08 11:45:57.624050
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "26304cbf3465"
down_revision: Union[str, Sequence[str], None] = "13cc806bed87"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create the accomplishments table."""
    op.create_table(
        "accomplishments",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("achieved_on", sa.Date(), nullable=True),
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
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    """Remove the accomplishments table."""
    op.drop_table("accomplishments")
