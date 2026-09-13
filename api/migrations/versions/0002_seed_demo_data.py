"""Fill the database with meaningful demonstration data.

Revision ID: 0002_seed
Revises: 0001_schema
"""

from collections.abc import Sequence
from datetime import UTC, datetime
from decimal import Decimal

import sqlalchemy as sa
from alembic import op

revision: str = "0002_seed"
down_revision: str | None = "0001_schema"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


components = sa.table(
    "components",
    sa.column("id", sa.Integer),
    sa.column("category", sa.String),
    sa.column("manufacturer", sa.String),
    sa.column("model", sa.String),
    sa.column("description", sa.Text),
    sa.column("specifications", sa.JSON),
)
offers = sa.table(
    "retail_offers",
    sa.column("id", sa.Integer),
    sa.column("component_id", sa.Integer),
    sa.column("retailer", sa.String),
    sa.column("price", sa.Numeric),
    sa.column("product_url", sa.String),
    sa.column("in_stock", sa.Boolean),
)
builds = sa.table(
    "builds",
    sa.column("id", sa.Integer),
    sa.column("name", sa.String),
    sa.column("owner_name", sa.String),
    sa.column("description", sa.Text),
    sa.column("is_public", sa.Boolean),
)
build_components = sa.table(
    "build_components",
    sa.column("build_id", sa.Integer),
    sa.column("component_id", sa.Integer),
)
reviews = sa.table(
    "reviews",
    sa.column("id", sa.Integer),
    sa.column("build_id", sa.Integer),
    sa.column("author_name", sa.String),
    sa.column("rating", sa.Integer),
    sa.column("comment", sa.Text),
    sa.column("created_at", sa.DateTime(timezone=True)),
)


def upgrade() -> None:
    op.bulk_insert(
        components,
        [
            {
                "id": 1,
                "category": "cpu",
                "manufacturer": "AMD",
                "model": "Ryzen 7 7800X3D",
                "description": "8 branduolių žaidimų procesorius.",
                "specifications": {"socket": "AM5", "cores": 8, "tdp_watts": 120},
            },
            {
                "id": 2,
                "category": "motherboard",
                "manufacturer": "MSI",
                "model": "MAG B650 TOMAHAWK WIFI",
                "description": "ATX formato AM5 pagrindinė plokštė.",
                "specifications": {"socket": "AM5", "memory_type": "DDR5", "form_factor": "ATX"},
            },
            {
                "id": 3,
                "category": "memory",
                "manufacturer": "Kingston",
                "model": "FURY Beast 32GB DDR5-6000",
                "description": "Dviejų 16 GB modulių komplektas.",
                "specifications": {"memory_type": "DDR5", "capacity_gb": 32},
            },
            {
                "id": 4,
                "category": "gpu",
                "manufacturer": "ASUS",
                "model": "Dual GeForce RTX 4070 SUPER",
                "description": "1440p raiškai skirta vaizdo plokštė.",
                "specifications": {"length_mm": 267, "recommended_psu_watts": 650, "vram_gb": 12},
            },
            {
                "id": 5,
                "category": "storage",
                "manufacturer": "Samsung",
                "model": "990 PRO 2TB",
                "description": "PCIe 4.0 NVMe SSD kaupiklis.",
                "specifications": {"capacity_gb": 2000, "interface": "NVMe PCIe 4.0"},
            },
            {
                "id": 6,
                "category": "psu",
                "manufacturer": "Corsair",
                "model": "RM750e",
                "description": "750 W 80 PLUS Gold maitinimo šaltinis.",
                "specifications": {"wattage": 750, "efficiency": "80 PLUS Gold"},
            },
            {
                "id": 7,
                "category": "case",
                "manufacturer": "Fractal Design",
                "model": "North",
                "description": "Gerai ventiliuojamas vidutinio dydžio korpusas.",
                "specifications": {
                    "supported_form_factors": ["ATX", "Micro-ATX", "Mini-ITX"],
                    "max_gpu_length_mm": 355,
                },
            },
            {
                "id": 8,
                "category": "cooler",
                "manufacturer": "Noctua",
                "model": "NH-D15 chromax.black",
                "description": "Didelio našumo orinis procesoriaus aušintuvas.",
                "specifications": {
                    "supported_sockets": ["AM5", "AM4", "LGA1700"],
                    "tdp_capacity_watts": 220,
                },
            },
            {
                "id": 9,
                "category": "cpu",
                "manufacturer": "Intel",
                "model": "Core i5-14600K",
                "description": "14 branduolių LGA1700 procesorius nesuderinamumo demonstracijai.",
                "specifications": {"socket": "LGA1700", "cores": 14, "tdp_watts": 181},
            },
        ],
    )

    offer_rows = []
    prices = [389, 219, 119, 669, 169, 129, 139, 119, 329]
    models = [
        "7800x3d",
        "b650",
        "ddr5-32gb",
        "rtx4070-super",
        "990pro-2tb",
        "rm750e",
        "fractal-north",
        "nh-d15",
        "14600k",
    ]
    for index, (price, slug) in enumerate(zip(prices, models, strict=True), start=1):
        offer_rows.extend(
            [
                {
                    "id": index * 2 - 1,
                    "component_id": index,
                    "retailer": "Kilobaitas",
                    "price": Decimal(str(price)),
                    "product_url": f"https://example.com/kilobaitas/{slug}",
                    "in_stock": True,
                },
                {
                    "id": index * 2,
                    "component_id": index,
                    "retailer": "Varle.lt",
                    "price": Decimal(str(price + 10)),
                    "product_url": f"https://example.com/varle/{slug}",
                    "in_stock": index != 4,
                },
            ]
        )
    op.bulk_insert(offers, offer_rows)

    op.bulk_insert(
        builds,
        [
            {
                "id": 1,
                "name": "Subalansuotas 1440p žaidimų PC",
                "owner_name": "Juozas",
                "description": "Pilnas, suderinamas žaidimų komplektas su dviem kainų pasiūlymais kiekvienai daliai.",
                "is_public": True,
            },
            {
                "id": 2,
                "name": "Nesuderinamas demonstracinis PC",
                "owner_name": "Demo naudotojas",
                "description": "LGA1700 procesorius įdėtas į AM5 plokštę, kad būtų parodytas suderinamumo perspėjimas.",
                "is_public": True,
            },
        ],
    )
    op.bulk_insert(
        build_components,
        [
            *({"build_id": 1, "component_id": component_id} for component_id in range(1, 9)),
            *({"build_id": 2, "component_id": component_id} for component_id in range(2, 10)),
        ],
    )
    op.bulk_insert(
        reviews,
        [
            {
                "id": 1,
                "build_id": 1,
                "author_name": "Mantas",
                "rating": 5,
                "comment": "Puikus kainos ir našumo santykis 1440p žaidimams.",
                "created_at": datetime(2026, 9, 13, 12, 0, tzinfo=UTC),
            },
            {
                "id": 2,
                "build_id": 1,
                "author_name": "Aistė",
                "rating": 4,
                "comment": "Geras komplektas, bet galima rinktis pigesnį aušintuvą.",
                "created_at": datetime(2026, 9, 13, 12, 5, tzinfo=UTC),
            },
        ],
    )

    connection = op.get_bind()
    for table_name in ("components", "retail_offers", "builds", "reviews"):
        connection.execute(
            sa.text(
                f"SELECT setval(pg_get_serial_sequence('{table_name}', 'id'), "
                f"COALESCE((SELECT MAX(id) FROM {table_name}), 1))"
            )
        )


def downgrade() -> None:
    op.execute(reviews.delete().where(reviews.c.id.in_([1, 2])))
    op.execute(build_components.delete().where(build_components.c.build_id.in_([1, 2])))
    op.execute(builds.delete().where(builds.c.id.in_([1, 2])))
    op.execute(offers.delete().where(offers.c.id.between(1, 18)))
    op.execute(components.delete().where(components.c.id.between(1, 9)))
