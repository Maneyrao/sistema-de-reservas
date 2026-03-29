from alembic import op
import sqlalchemy as sa

revision = "97a9cbc1c82d"
down_revision = "aa17bd10ec95"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("customer", schema=None) as batch_op:
        batch_op.add_column(sa.Column("email", sa.String(), nullable=True))
        batch_op.create_index("ix_customer_email", ["email"])
        batch_op.create_unique_constraint("uq_customer_email", ["email"])


def downgrade():
    with op.batch_alter_table("customer", schema=None) as batch_op:
        batch_op.drop_constraint("uq_customer_email", type_="unique")
        batch_op.drop_index("ix_customer_email")
        batch_op.drop_column("email")
