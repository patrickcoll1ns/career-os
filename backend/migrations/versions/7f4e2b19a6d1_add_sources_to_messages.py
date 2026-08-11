"""add sources to messages

Revision ID: 7f4e2b19a6d1
Revises: c86cbb6d6aef
Create Date: 2026-08-10 23:30:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "7f4e2b19a6d1"
down_revision: Union[str, Sequence[str], None] = "c86cbb6d6aef"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Persist document references used for assistant responses."""
    op.add_column(
        "messages",
        sa.Column(
            "sources",
            sa.JSON(),
            server_default=sa.text("'[]'::json"),
            nullable=False,
        ),
    )


def downgrade() -> None:
    """Remove persisted document references from messages."""
    op.drop_column("messages", "sources")
