"""add admin dashboard core

Revision ID: d14e9f2137ac
Revises: c6f8e2d1a9b4
Create Date: 2026-03-09
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "d14e9f2137ac"
down_revision: Union[str, Sequence[str], None] = "c6f8e2d1a9b4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("ALTER TYPE bookingstatus ADD VALUE IF NOT EXISTS 'pending'")
        op.execute("ALTER TYPE bookingstatus ADD VALUE IF NOT EXISTS 'completed'")
        op.execute("ALTER TYPE bookingstatus ADD VALUE IF NOT EXISTS 'no_show'")

    with op.batch_alter_table("booking", schema=None) as batch_op:
        batch_op.add_column(sa.Column("notes", sa.String(length=500), nullable=True))
        batch_op.add_column(sa.Column("canceled_reason", sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column("canceled_at", sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column("rescheduled_from_booking_id", sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            "fk_booking_rescheduled_from_booking_id",
            "booking",
            ["rescheduled_from_booking_id"],
            ["id"],
        )
        batch_op.create_index(
            "ix_booking_business_start_datetime",
            ["business_id", "start_datetime"],
            unique=False,
        )

    op.create_table(
        "admin_user",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("business_id", sa.Integer(), sa.ForeignKey("business.id"), nullable=False),
        sa.Column("full_name", sa.String(length=120), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("role", sa.String(length=40), nullable=False, server_default=sa.text("'owner'")),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("business_id", "email", name="uq_admin_user_business_email"),
    )
    op.create_index("ix_admin_user_email", "admin_user", ["email"], unique=False)

    op.create_table(
        "time_block",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("business_id", sa.Integer(), sa.ForeignKey("business.id"), nullable=False),
        sa.Column("staff_id", sa.Integer(), sa.ForeignKey("staff.id"), nullable=True),
        sa.Column("start_datetime", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_datetime", sa.DateTime(timezone=True), nullable=False),
        sa.Column("reason", sa.String(length=255), nullable=True),
        sa.Column("notes", sa.String(length=500), nullable=True),
        sa.Column("created_by_admin_id", sa.Integer(), sa.ForeignKey("admin_user.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("end_datetime > start_datetime", name="ck_time_block_end_after_start"),
    )
    op.create_index(
        "ix_time_block_business_range",
        "time_block",
        ["business_id", "start_datetime", "end_datetime"],
        unique=False,
    )
    op.create_index(
        "ix_time_block_staff_range",
        "time_block",
        ["staff_id", "start_datetime", "end_datetime"],
        unique=False,
    )

    op.create_table(
        "audit_log",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("business_id", sa.Integer(), sa.ForeignKey("business.id"), nullable=False),
        sa.Column("admin_user_id", sa.Integer(), sa.ForeignKey("admin_user.id"), nullable=True),
        sa.Column("action", sa.String(length=80), nullable=False),
        sa.Column("entity_type", sa.String(length=80), nullable=False),
        sa.Column("entity_id", sa.String(length=120), nullable=False),
        sa.Column("payload_json", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index(
        "ix_audit_log_business_created_at",
        "audit_log",
        ["business_id", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_audit_log_business_created_at", table_name="audit_log")
    op.drop_table("audit_log")

    op.drop_index("ix_time_block_staff_range", table_name="time_block")
    op.drop_index("ix_time_block_business_range", table_name="time_block")
    op.drop_table("time_block")

    op.drop_index("ix_admin_user_email", table_name="admin_user")
    op.drop_table("admin_user")

    with op.batch_alter_table("booking", schema=None) as batch_op:
        batch_op.drop_index("ix_booking_business_start_datetime")
        batch_op.drop_constraint("fk_booking_rescheduled_from_booking_id", type_="foreignkey")
        batch_op.drop_column("rescheduled_from_booking_id")
        batch_op.drop_column("updated_at")
        batch_op.drop_column("canceled_at")
        batch_op.drop_column("canceled_reason")
        batch_op.drop_column("notes")
