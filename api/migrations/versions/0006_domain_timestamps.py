"""Align domain timestamps with the timezone-aware ORM models.

Existing deployment timestamps are UTC. Explicit conversion preserves these
values even when the migration connection uses a different session timezone.
Auth session and JWT timestamps are unchanged.
"""

import sqlalchemy as sa
from alembic import op

revision = "0006_timestamps"
down_revision = "0005_user_status"
branch_labels = None
depends_on = None


def upgrade() -> None:
    for table in ("builds", "components", "retail_offers"):
        for column in ("created_at", "updated_at"):
            op.alter_column(
                table,
                column,
                existing_type=sa.DateTime(),
                type_=sa.DateTime(timezone=True),
                existing_nullable=False,
                postgresql_using=f"{column} AT TIME ZONE 'UTC'",
            )


def downgrade() -> None:
    for table in ("builds", "components", "retail_offers"):
        for column in ("created_at", "updated_at"):
            op.alter_column(
                table,
                column,
                existing_type=sa.DateTime(timezone=True),
                type_=sa.DateTime(),
                existing_nullable=False,
                postgresql_using=f"{column} AT TIME ZONE 'UTC'",
            )
