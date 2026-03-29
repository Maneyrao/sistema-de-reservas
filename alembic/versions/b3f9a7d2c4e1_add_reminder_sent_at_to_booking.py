"""add reminder_sent_at to booking

Revision ID: b3f9a7d2c4e1
Revises: 97a9cbc1c82d
Create Date: 2026-03-07
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "b3f9a7d2c4e1"
down_revision: Union[str, Sequence[str], None] = "97a9cbc1c82d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "booking",
        sa.Column("reminder_sent_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("booking", "reminder_sent_at")
