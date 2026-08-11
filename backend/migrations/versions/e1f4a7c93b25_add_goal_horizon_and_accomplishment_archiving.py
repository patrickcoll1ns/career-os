"""add goal horizon and accomplishment archiving

Revision ID: e1f4a7c93b25
Revises: d9a2c7e45f10
Create Date: 2026-08-11 19:05:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e1f4a7c93b25"
down_revision: Union[str, Sequence[str], None] = "d9a2c7e45f10"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add the goal planning horizon and soft-delete support for accomplishments."""
    op.add_column(
        "goals",
        sa.Column(
            "horizon",
            sa.String(length=20),
            nullable=False,
            server_default="short_term",
        ),
    )
    op.create_check_constraint(
        "ck_goals_horizon",
        "goals",
        "horizon IN ('short_term', 'long_term')",
    )
    # Existing goals predate the field. Seed each one from how far out its target
    # date is so the first view is roughly right; the field is user-owned after
    # this, and undated goals stay short_term.
    op.execute(
        """
        UPDATE goals
        SET horizon = 'long_term'
        WHERE target_date IS NOT NULL
          AND target_date > CURRENT_DATE + INTERVAL '6 months'
        """
    )

    op.add_column(
        "accomplishments",
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    """Remove the horizon column and accomplishment archiving."""
    op.drop_column("accomplishments", "archived_at")
    op.drop_constraint("ck_goals_horizon", "goals", type_="check")
    op.drop_column("goals", "horizon")
