from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, model_validator

from app.models.domain import ComponentCategory

REQUIRED_SPECIFICATIONS: dict[ComponentCategory, set[str]] = {
    ComponentCategory.CPU: {"socket", "cores", "tdp_watts"},
    ComponentCategory.MOTHERBOARD: {"socket", "memory_type", "form_factor"},
    ComponentCategory.MEMORY: {"memory_type", "capacity_gb"},
    ComponentCategory.GPU: {"length_mm", "recommended_psu_watts"},
    ComponentCategory.STORAGE: {"capacity_gb", "interface"},
    ComponentCategory.PSU: {"wattage"},
    ComponentCategory.CASE: {"supported_form_factors", "max_gpu_length_mm"},
    ComponentCategory.COOLER: {"supported_sockets", "tdp_capacity_watts"},
}


class OfferInput(BaseModel):
    retailer: str = Field(min_length=2, max_length=100, examples=["Kilobaitas"])
    price: Decimal = Field(gt=0, max_digits=10, decimal_places=2, examples=[299.99])
    product_url: HttpUrl
    in_stock: bool = True


class OfferRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    retailer: str
    price: Decimal
    product_url: str
    in_stock: bool


class ComponentInput(BaseModel):
    category: ComponentCategory
    manufacturer: str = Field(min_length=2, max_length=80, examples=["AMD"])
    model: str = Field(min_length=2, max_length=120, examples=["Ryzen 7 7800X3D"])
    description: str | None = Field(default=None, max_length=2000)
    specifications: dict[str, Any]
    offers: list[OfferInput] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_required_specifications(self) -> "ComponentInput":
        missing = REQUIRED_SPECIFICATIONS[self.category] - self.specifications.keys()
        if missing:
            fields = ", ".join(sorted(missing))
            raise ValueError(f"Missing specifications for {self.category.value}: {fields}")
        return self


class ComponentCreate(ComponentInput):
    pass


class ComponentReplace(ComponentInput):
    pass


class ComponentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    category: ComponentCategory
    manufacturer: str
    model: str
    description: str | None
    specifications: dict[str, Any]
    offers: list[OfferRead]
    created_at: datetime
    updated_at: datetime
