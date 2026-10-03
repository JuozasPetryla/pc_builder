from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.common import ApiInput
from app.schemas.component import ComponentRead
from app.schemas.review import ReviewRead


class BuildInput(ApiInput):
    name: str = Field(min_length=3, max_length=120, examples=["1440p Gaming PC"])
    description: str | None = Field(default=None, max_length=2000)
    is_public: bool = Field(
        default=False,
        description="Viešą komplektą gali skaityti visi prisijungę naudotojai; privatų – tik savininkas.",
    )


class BuildCreate(BuildInput):
    pass


class BuildReplace(BuildInput):
    pass


class BuildRead(BaseModel):
    id: int
    name: str
    owner_id: int | None
    owner_name: str
    description: str | None
    is_public: bool
    components: list[ComponentRead]
    reviews: list[ReviewRead]
    created_at: datetime
    updated_at: datetime
    links: "BuildLinks"


class BuildLinks(BaseModel):
    self: str
    components: str
    reviews: str
