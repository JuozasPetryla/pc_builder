"""Users, revocable sessions and resource ownership.

Existing records retain their display names and NULL ownership: they are
admin-managed and cannot be claimed by registering a matching username.
"""

import sqlalchemy as sa
from alembic import op

revision = "0004_auth"
down_revision = "0003_builds"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("username", sa.String(80), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("role", sa.String(16), nullable=False),
        sa.CheckConstraint("role IN ('user', 'moderator', 'admin')", name="valid_role"),
    )
    op.create_table(
        "auth_sessions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("refresh_hash", sa.String(64), nullable=False, unique=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked", sa.Boolean(), nullable=False),
    )
    op.create_index("ix_auth_sessions_user_id", "auth_sessions", ["user_id"])
    for table, column in [("builds", "owner_id"), ("reviews", "author_id")]:
        op.add_column(table, sa.Column(column, sa.Integer(), nullable=True))
        op.create_foreign_key(f"fk_{table}_{column}_users", table, "users", [column], ["id"])
        op.create_index(f"ix_{table}_{column}", table, [column])


def downgrade() -> None:
    for table, column in [("reviews", "author_id"), ("builds", "owner_id")]:
        op.drop_index(f"ix_{table}_{column}", table)
        op.drop_constraint(f"fk_{table}_{column}_users", table, type_="foreignkey")
        op.drop_column(table, column)
    op.drop_table("auth_sessions")
    op.drop_table("users")
