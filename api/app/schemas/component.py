from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, Field, HttpUrl

from app.models.domain import ComponentCategory
from app.schemas.common import ApiInput


class OfferInput(ApiInput):
    retailer: str = Field(min_length=2, max_length=100, examples=["Kilobaitas"])
    price: Decimal = Field(
        gt=0,
        max_digits=10,
        decimal_places=2,
        examples=["299.99"],
        description="Teigiama kaina, iki 2 skaitmenų po kablelio. Atsakyme — JSON eilutė.",
    )
    product_url: HttpUrl = Field(
        max_length=500, examples=["https://example.com/products/ryzen-7-7800x3d"]
    )
    in_stock: bool = True


class OfferRead(BaseModel):
    id: int
    component_id: int
    retailer: str
    price: Decimal
    product_url: str
    in_stock: bool
    links: "OfferLinks"


class OfferLinks(BaseModel):
    self: str
    component: str
    build: str


class OfferCreate(OfferInput):
    pass


class OfferReplace(OfferInput):
    pass


class ComponentInput(ApiInput):
    category: ComponentCategory = Field(
        description="Komponento tipas. Viename komplekte — vienas komponentas kiekvienai kategorijai.",
        examples=["cpu"],
    )
    manufacturer: str = Field(min_length=2, max_length=80, examples=["AMD"])
    model: str = Field(min_length=2, max_length=120, examples=["Ryzen 7 7800X3D"])
    description: str | None = Field(default=None, max_length=2000)
    specifications: dict[str, Any] = Field(
        min_length=1,
        description="Netuščias JSON objektas; kategorijai specifiniai raktai nėra privalomi.",
        examples=[{"socket": "AM5", "cores": 8, "tdp_w": 120}],
    )


class ComponentCreate(ComponentInput):
    pass


class ComponentReplace(ComponentInput):
    pass


class ComponentRead(BaseModel):
    id: int
    build_id: int
    category: ComponentCategory
    manufacturer: str
    model: str
    description: str | None
    specifications: dict[str, Any]
    offers: list[OfferRead]
    created_at: datetime
    updated_at: datetime
    links: "ComponentLinks"


class ComponentLinks(BaseModel):
    self: str
    build: str
    offers: str
