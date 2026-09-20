"""Replace shared catalog links with Build -> Component -> RetailOffer ownership.

Revision ID: 0003_builds
Revises: 0002_seed
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003_builds"
down_revision: str | None = "0002_seed"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _copy_component(connection, components, offers, source_id: int, build_id: int) -> int:
    source = dict(
        connection.execute(sa.select(components).where(components.c.id == source_id))
        .mappings()
        .one()
    )
    source.pop("id")
    source["build_id"] = build_id
    component_id = connection.scalar(
        components.insert().values(**source).returning(components.c.id)
    )
    for offer in connection.execute(
        sa.select(offers).where(offers.c.component_id == source_id)
    ).mappings():
        values = dict(offer)
        values.pop("id")
        values["component_id"] = component_id
        connection.execute(offers.insert().values(**values))
    return component_id


def upgrade() -> None:
    connection = op.get_bind()
    op.add_column("components", sa.Column("build_id", sa.Integer(), nullable=True))
    op.drop_constraint("uq_component_manufacturer_model", "components", type_="unique")
    metadata = sa.MetaData()
    components = sa.Table("components", metadata, autoload_with=connection)
    offers = sa.Table("retail_offers", metadata, autoload_with=connection)
    builds = sa.Table("builds", metadata, autoload_with=connection)
    reviews = sa.Table("reviews", metadata, autoload_with=connection)
    links = sa.Table("build_components", metadata, autoload_with=connection)

    # Keep original IDs for the first owner. Other owners get independent
    # snapshots, including their own copies of every retailer offer.
    originals = list(connection.execute(sa.select(components).order_by(components.c.id)).mappings())
    for component in originals:
        owners = list(
            connection.scalars(
                sa.select(links.c.build_id)
                .where(links.c.component_id == component["id"])
                .order_by(links.c.build_id)
            )
        )
        if not owners:
            # Preserve unassigned catalog data in a meaningful draft build.
            owners = [
                connection.scalar(
                    builds.insert()
                    .values(
                        name=("Juodraštis: " + component["model"])[:120],
                        owner_name="Perkelti katalogo duomenys",
                        description="Anksčiau nepriskirtas komponentas, išsaugotas keičiant hierarchiją.",
                        is_public=False,
                    )
                    .returning(builds.c.id)
                )
            ]
        connection.execute(
            components.update().where(components.c.id == component["id"]).values(build_id=owners[0])
        )
        for owner in owners[1:]:
            _copy_component(connection, components, offers, component["id"], owner)

    op.alter_column("components", "build_id", nullable=False)
    op.create_foreign_key(
        "fk_components_build_id_builds",
        "components",
        "builds",
        ["build_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_index("ix_components_build_id", "components", ["build_id"])
    op.create_unique_constraint(
        "uq_component_build_category", "components", ["build_id", "category"]
    )
    op.drop_table("build_components")

    # Add only missing demonstration rows, without overwriting existing IDs.
    templates = list(
        connection.scalars(sa.select(sa.func.min(components.c.id)).group_by(components.c.category))
    )
    examples = [
        ("Darbo ir mokslų PC", "Ieva", "Komplektas programavimui ir kasdieniam darbui.", True),
        ("Kūrėjo darbo stotis", "Tomas", "Komplektas virtualioms mašinoms ir kūrybai.", True),
        ("Namų žaidimų kompiuteris", "Rūta", "Komplektas mokslams ir 1440p žaidimams.", False),
        ("Vaizdo montavimo PC", "Mantas", "Komplektas vaizdo apdorojimo užduotims.", True),
        ("Programuotojo PC", "Aistė", "Komplektas darbui su kūrimo aplinkomis.", False),
    ]
    build_count = connection.scalar(sa.select(sa.func.count()).select_from(builds))
    for name, owner, description, is_public in examples[: max(0, 5 - build_count)]:
        build_id = connection.scalar(
            builds.insert()
            .values(name=name, owner_name=owner, description=description, is_public=is_public)
            .returning(builds.c.id)
        )
        for component_id in templates:
            _copy_component(connection, components, offers, component_id, build_id)

    review_examples = [
        ("Lukas", 4, "Geras dalių pasirinkimas, prieš pirkimą patikrinčiau lizdų suderinamumą."),
        ("Eglė", 5, "Pakanka atminties kasdieniam darbui ir mokslams."),
        ("Paulius", 4, "Spartus kaupiklis ir gera bazė tolesniam atnaujinimui."),
        ("Dovilė", 5, "Patinka galimybė palyginti kelių pardavėjų kainas."),
        ("Rokas", 4, "Rinkčiausi šį komplektą darbui ir laisvalaikiui."),
    ]
    build_ids = list(connection.scalars(sa.select(builds.c.id).order_by(builds.c.id)))
    review_count = connection.scalar(sa.select(sa.func.count()).select_from(reviews))
    for index, (author, rating, comment) in enumerate(review_examples[: max(0, 5 - review_count)]):
        connection.execute(
            reviews.insert().values(
                build_id=build_ids[index % len(build_ids)],
                author_name=author,
                rating=rating,
                comment=comment,
            )
        )


def downgrade() -> None:
    # Independent snapshots may already contain different specifications and
    # prices. Merging them into one globally unique catalog row would lose data.
    raise RuntimeError(
        "0003_builds atšaukimui reikalinga prieš migraciją sukurta DB atsarginė kopija: "
        "atskirų komplektų komponentų automatiškai sujungti neprarandant duomenų negalima."
    )
