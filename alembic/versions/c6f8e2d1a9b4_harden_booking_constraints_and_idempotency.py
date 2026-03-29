"""harden booking constraints and idempotency

Revision ID: c6f8e2d1a9b4
Revises: b3f9a7d2c4e1
Create Date: 2026-03-09
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "c6f8e2d1a9b4"
down_revision: Union[str, Sequence[str], None] = "b3f9a7d2c4e1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("booking", schema=None) as batch_op:
        batch_op.add_column(sa.Column("idempotency_key", sa.String(length=120), nullable=True))
        batch_op.create_check_constraint(
            "ck_booking_end_after_start",
            "end_datetime > start_datetime",
        )
        batch_op.create_unique_constraint(
            "uq_booking_business_idempotency_key",
            ["business_id", "idempotency_key"],
        )

    op.create_index(
        "ix_booking_staff_status_start",
        "booking",
        ["staff_id", "status", "start_datetime"],
        unique=False,
    )
    op.create_index(
        "ix_booking_reminder_lookup",
        "booking",
        ["status", "reminder_sent_at", "start_datetime"],
        unique=False,
    )

    with op.batch_alter_table("service", schema=None) as batch_op:
        batch_op.create_unique_constraint(
            "uq_service_business_slug",
            ["business_id", "slug"],
        )

    with op.batch_alter_table("availability_rule", schema=None) as batch_op:
        batch_op.create_unique_constraint(
            "uq_availability_rule_slot",
            ["staff_id", "weekday", "start_time", "end_time"],
        )
        batch_op.create_check_constraint(
            "ck_availability_weekday",
            "weekday >= 0 AND weekday <= 6",
        )
        batch_op.create_check_constraint(
            "ck_availability_start_before_end",
            "start_time < end_time",
        )

    op.create_index(
        "uq_customer_phone_not_empty",
        "customer",
        ["phone"],
        unique=True,
        sqlite_where=sa.text("phone IS NOT NULL AND phone != ''"),
        postgresql_where=sa.text("phone IS NOT NULL AND btrim(phone) <> ''"),
    )


def downgrade() -> None:
    op.drop_index("uq_customer_phone_not_empty", table_name="customer")

    with op.batch_alter_table("availability_rule", schema=None) as batch_op:
        batch_op.drop_constraint("ck_availability_start_before_end", type_="check")
        batch_op.drop_constraint("ck_availability_weekday", type_="check")
        batch_op.drop_constraint("uq_availability_rule_slot", type_="unique")

    with op.batch_alter_table("service", schema=None) as batch_op:
        batch_op.drop_constraint("uq_service_business_slug", type_="unique")

    op.drop_index("ix_booking_reminder_lookup", table_name="booking")
    op.drop_index("ix_booking_staff_status_start", table_name="booking")

    with op.batch_alter_table("booking", schema=None) as batch_op:
        batch_op.drop_constraint("uq_booking_business_idempotency_key", type_="unique")
        batch_op.drop_constraint("ck_booking_end_after_start", type_="check")
        batch_op.drop_column("idempotency_key")
