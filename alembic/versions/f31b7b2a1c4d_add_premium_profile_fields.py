"""add premium profile fields

Revision ID: f31b7b2a1c4d
Revises: ea9f02b18f6c
Create Date: 2026-03-28
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "f31b7b2a1c4d"
down_revision: Union[str, Sequence[str], None] = "ea9f02b18f6c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("business", schema=None) as batch_op:
        batch_op.add_column(sa.Column("hero_title", sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column("hero_description", sa.String(length=1000), nullable=True))
        batch_op.add_column(sa.Column("announcement", sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column("booking_note", sa.String(length=255), nullable=True))

    with op.batch_alter_table("staff", schema=None) as batch_op:
        batch_op.add_column(sa.Column("title", sa.String(length=120), nullable=True))
        batch_op.add_column(sa.Column("bio", sa.String(length=500), nullable=True))
        batch_op.add_column(sa.Column("avatar_url", sa.String(length=500), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("staff", schema=None) as batch_op:
        batch_op.drop_column("avatar_url")
        batch_op.drop_column("bio")
        batch_op.drop_column("title")

    with op.batch_alter_table("business", schema=None) as batch_op:
        batch_op.drop_column("booking_note")
        batch_op.drop_column("announcement")
        batch_op.drop_column("hero_description")
        batch_op.drop_column("hero_title")
