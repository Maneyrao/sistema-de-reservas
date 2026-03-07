from alembic import op
import sqlalchemy as sa

revision = "97a9cbc1c82d"
down_revision = "aa17bd10ec95"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "customer",
        sa.Column("email", sa.String(), nullable=True)
    )

    op.create_index(
        "ix_customer_email",
        "customer",
        ["email"]
    )

    op.create_unique_constraint(
        "uq_customer_email",
        "customer",
        ["email"]
    )


def downgrade():
    op.drop_constraint("uq_customer_email", "customer", type_="unique")
    op.drop_index("ix_customer_email", table_name="customer")
    op.drop_column("customer", "email")
