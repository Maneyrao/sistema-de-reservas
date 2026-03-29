"""add business profile and staff_service

Revision ID: ea9f02b18f6c
Revises: d14e9f2137ac
Create Date: 2026-03-28
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "ea9f02b18f6c"
down_revision: Union[str, Sequence[str], None] = "d14e9f2137ac"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("business", schema=None) as batch_op:
        batch_op.add_column(sa.Column("tagline", sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column("address", sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column("phone", sa.String(length=40), nullable=True))
        batch_op.add_column(sa.Column("instagram_url", sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column("maps_url", sa.String(length=500), nullable=True))

    with op.batch_alter_table("service", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("price_amount", sa.Integer(), nullable=False, server_default=sa.text("0"))
        )
        batch_op.add_column(
            sa.Column("price_currency", sa.String(length=3), nullable=False, server_default=sa.text("'ARS'"))
        )

    op.create_table(
        "staff_service",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("staff_id", sa.Integer(), sa.ForeignKey("staff.id"), nullable=False),
        sa.Column("service_id", sa.Integer(), sa.ForeignKey("service.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("staff_id", "service_id", name="uq_staff_service_pair"),
    )


def downgrade() -> None:
    op.drop_table("staff_service")

    with op.batch_alter_table("service", schema=None) as batch_op:
        batch_op.drop_column("price_currency")
        batch_op.drop_column("price_amount")

    with op.batch_alter_table("business", schema=None) as batch_op:
        batch_op.drop_column("maps_url")
        batch_op.drop_column("instagram_url")
        batch_op.drop_column("phone")
        batch_op.drop_column("address")
        batch_op.drop_column("tagline")
