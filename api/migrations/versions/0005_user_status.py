"""Add account blocking without changing JWT or session storage."""

import sqlalchemy as sa
from alembic import op

revision = "0005_user_status"
down_revision = "0004_auth"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users", sa.Column("is_blocked", sa.Boolean(), nullable=False, server_default=sa.false())
    )


def downgrade() -> None:
    op.drop_column("users", "is_blocked")
