from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import StrEnum

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class ComponentCategory(StrEnum):
    CPU = "cpu"
    MOTHERBOARD = "motherboard"
    MEMORY = "memory"
    GPU = "gpu"
    STORAGE = "storage"
    PSU = "psu"
    CASE = "case"
    COOLER = "cooler"


class CatalogComponent(TimestampMixin, Base):
    __tablename__ = "catalog_components"
    __table_args__ = (UniqueConstraint("id", "category", name="uq_catalog_id_category"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    category: Mapped[str] = mapped_column(String(32), index=True)
    manufacturer: Mapped[str] = mapped_column(String(80))
    model: Mapped[str] = mapped_column(String(120))
    description: Mapped[str | None] = mapped_column(Text)
    specifications: Mapped[dict] = mapped_column(JSON, default=dict)
    # Old private component data must not become a public catalog entry.
    legacy_build_id: Mapped[int | None] = mapped_column(
        ForeignKey("builds.id", ondelete="CASCADE"), index=True
    )
    offers: Mapped[list[RetailOffer]] = relationship(
        back_populates="component", cascade="all, delete-orphan", lazy="selectin"
    )


class Component(TimestampMixin, Base):
    """One selection in a build, referencing shared catalog data."""

    __tablename__ = "components"
    __table_args__ = (
        UniqueConstraint("build_id", "category", name="uq_component_build_category"),
        ForeignKeyConstraint(
            ["catalog_component_id", "category"],
            ["catalog_components.id", "catalog_components.category"],
            name="fk_component_catalog_category",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    build_id: Mapped[int] = mapped_column(ForeignKey("builds.id", ondelete="CASCADE"), index=True)
    catalog_component_id: Mapped[int] = mapped_column(index=True)
    category: Mapped[str] = mapped_column(String(32), index=True)
    build: Mapped[Build] = relationship(back_populates="components", foreign_keys=[build_id])
    catalog: Mapped[CatalogComponent] = relationship(lazy="joined")


class RetailOffer(TimestampMixin, Base):
    __tablename__ = "retail_offers"
    __table_args__ = (
        CheckConstraint("price > 0", name="positive_price"),
        UniqueConstraint("component_id", "retailer", name="uq_offer_component_retailer"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    component_id: Mapped[int] = mapped_column(
        ForeignKey("catalog_components.id", ondelete="CASCADE"), index=True
    )
    retailer: Mapped[str] = mapped_column(String(100))
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    product_url: Mapped[str] = mapped_column(String(500))
    in_stock: Mapped[bool] = mapped_column(Boolean, default=True)

    component: Mapped[CatalogComponent] = relationship(back_populates="offers")


class Build(TimestampMixin, Base):
    __tablename__ = "builds"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    owner_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), index=True)
    owner_name: Mapped[str] = mapped_column(String(80), index=True)
    description: Mapped[str | None] = mapped_column(Text)
    is_public: Mapped[bool] = mapped_column(Boolean, default=False, index=True)

    components: Mapped[list[Component]] = relationship(
        back_populates="build", cascade="all, delete-orphan", lazy="selectin"
    )
    reviews: Mapped[list[Review]] = relationship(
        back_populates="build", cascade="all, delete-orphan", lazy="selectin"
    )


class Review(Base):
    __tablename__ = "reviews"
    __table_args__ = (CheckConstraint("rating BETWEEN 1 AND 5", name="valid_rating"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    build_id: Mapped[int] = mapped_column(ForeignKey("builds.id", ondelete="CASCADE"), index=True)
    author_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), index=True)
    author_name: Mapped[str] = mapped_column(String(80))
    rating: Mapped[int] = mapped_column(Integer)
    comment: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    build: Mapped[Build] = relationship(back_populates="reviews")
