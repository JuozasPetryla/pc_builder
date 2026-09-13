"""Create the PC Builder database schema.

Revision ID: 0001_schema
Revises:
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001_schema"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "components",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("category", sa.String(length=32), nullable=False),
        sa.Column("manufacturer", sa.String(length=80), nullable=False),
        sa.Column("model", sa.String(length=120), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("specifications", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_components"),
        sa.UniqueConstraint("manufacturer", "model", name="uq_component_manufacturer_model"),
    )
    op.create_index("ix_components_category", "components", ["category"])

    op.create_table(
        "builds",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("owner_name", sa.String(length=80), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_public", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_builds"),
    )
    op.create_index("ix_builds_owner_name", "builds", ["owner_name"])
    op.create_index("ix_builds_is_public", "builds", ["is_public"])

    op.create_table(
        "retail_offers",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("component_id", sa.Integer(), nullable=False),
        sa.Column("retailer", sa.String(length=100), nullable=False),
        sa.Column("price", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("product_url", sa.String(length=500), nullable=False),
        sa.Column("in_stock", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("price > 0", name="ck_retail_offers_positive_price"),
        sa.ForeignKeyConstraint(
            ["component_id"], ["components.id"], ondelete="CASCADE", name="fk_offer_component"
        ),
        sa.PrimaryKeyConstraint("id", name="pk_retail_offers"),
        sa.UniqueConstraint("component_id", "retailer", name="uq_offer_component_retailer"),
    )
    op.create_index("ix_retail_offers_component_id", "retail_offers", ["component_id"])

    op.create_table(
        "build_components",
        sa.Column("build_id", sa.Integer(), nullable=False),
        sa.Column("component_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["build_id"], ["builds.id"], ondelete="CASCADE", name="fk_build_component_build"
        ),
        sa.ForeignKeyConstraint(
            ["component_id"],
            ["components.id"],
            ondelete="CASCADE",
            name="fk_build_component_component",
        ),
        sa.PrimaryKeyConstraint("build_id", "component_id", name="pk_build_components"),
    )

    op.create_table(
        "reviews",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("build_id", sa.Integer(), nullable=False),
        sa.Column("author_name", sa.String(length=80), nullable=False),
        sa.Column("rating", sa.Integer(), nullable=False),
        sa.Column("comment", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint("rating BETWEEN 1 AND 5", name="ck_reviews_valid_rating"),
        sa.ForeignKeyConstraint(
            ["build_id"], ["builds.id"], ondelete="CASCADE", name="fk_review_build"
        ),
        sa.PrimaryKeyConstraint("id", name="pk_reviews"),
    )
    op.create_index("ix_reviews_build_id", "reviews", ["build_id"])


def downgrade() -> None:
    op.drop_index("ix_reviews_build_id", table_name="reviews")
    op.drop_table("reviews")
    op.drop_table("build_components")
    op.drop_index("ix_retail_offers_component_id", table_name="retail_offers")
    op.drop_table("retail_offers")
    op.drop_index("ix_builds_is_public", table_name="builds")
    op.drop_index("ix_builds_owner_name", table_name="builds")
    op.drop_table("builds")
    op.drop_index("ix_components_category", table_name="components")
    op.drop_table("components")
