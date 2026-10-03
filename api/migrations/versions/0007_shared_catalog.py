"""Move specifications and offers to a shared catalog, preserving build selections.

Revision ID: 0007_catalog
Revises: 0006_timestamps
"""

import sqlalchemy as sa
from alembic import op

revision = "0007_catalog"
down_revision = "0006_timestamps"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "catalog_components",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("category", sa.String(32), nullable=False),
        sa.Column("manufacturer", sa.String(80), nullable=False),
        sa.Column("model", sa.String(120), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("specifications", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "legacy_build_id",
            sa.Integer(),
            sa.ForeignKey("builds.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.UniqueConstraint("id", "category", name="uq_catalog_id_category"),
    )
    op.create_index("ix_catalog_components_category", "catalog_components", ["category"])
    op.create_index(
        "ix_catalog_components_legacy_build_id", "catalog_components", ["legacy_build_id"]
    )
    op.execute(
        sa.text("""
        INSERT INTO catalog_components
            (id, category, manufacturer, model, description, specifications, created_at, updated_at, legacy_build_id)
        SELECT c.id, c.category, c.manufacturer, c.model, c.description, c.specifications,
               c.created_at, c.updated_at, CASE WHEN b.is_public THEN NULL ELSE b.id END
        FROM components c JOIN builds b ON b.id = c.build_id
    """)
    )
    op.execute(
        sa.text(
            "SELECT setval(pg_get_serial_sequence('catalog_components', 'id'), COALESCE(MAX(id), 1), MAX(id) IS NOT NULL) FROM catalog_components"
        )
    )
    op.add_column("components", sa.Column("catalog_component_id", sa.Integer(), nullable=True))
    op.execute(sa.text("UPDATE components SET catalog_component_id = id"))
    op.alter_column("components", "catalog_component_id", nullable=False)
    op.create_index("ix_components_catalog_component_id", "components", ["catalog_component_id"])
    op.create_foreign_key(
        "fk_component_catalog_category",
        "components",
        "catalog_components",
        ["catalog_component_id", "category"],
        ["id", "category"],
    )
    op.drop_constraint("fk_offer_component", "retail_offers", type_="foreignkey")
    op.create_foreign_key(
        "fk_retail_offers_component_id_catalog_components",
        "retail_offers",
        "catalog_components",
        ["component_id"],
        ["id"],
        ondelete="CASCADE",
    )
    for name in ["manufacturer", "model", "description", "specifications"]:
        op.drop_column("components", name)


def downgrade():
    raise RuntimeError(
        "0007_catalog: atšaukimui atkurkite DB kopiją; bendrų įrašų negalima grąžinti į nepriklausomas kopijas neprarandant ryšių."
    )
