from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.component import ComponentRead
from app.schemas.review import ReviewRead


class BuildInput(BaseModel):
    name: str = Field(min_length=3, max_length=120, examples=["1440p Gaming PC"])
    owner_name: str = Field(min_length=2, max_length=80, examples=["Juozas"])
    description: str | None = Field(default=None, max_length=2000)
    is_public: bool = False
    component_ids: list[int] = Field(default_factory=list, max_length=8)

    @field_validator("component_ids")
    @classmethod
    def component_ids_must_be_unique(cls, value: list[int]) -> list[int]:
        if len(value) != len(set(value)):
            raise ValueError("component_ids must be unique")
        return value


class BuildCreate(BuildInput):
    pass


class BuildReplace(BuildInput):
    pass


class CompatibilityIssue(BaseModel):
    code: str
    message: str
    component_ids: list[int]


class CompatibilityRead(BaseModel):
    build_id: int
    compatible: bool
    complete: bool
    total_price: Decimal
    missing_categories: list[str]
    issues: list[CompatibilityIssue]


class BuildRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    owner_name: str
    description: str | None
    is_public: bool
    components: list[ComponentRead]
    reviews: list[ReviewRead]
    compatibility: CompatibilityRead
    created_at: datetime
    updated_at: datetime
