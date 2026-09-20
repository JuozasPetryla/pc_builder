from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.common import ApiInput


class ReviewCreate(ApiInput):
    author_name: str = Field(min_length=2, max_length=80, examples=["Mantas"])
    rating: int = Field(ge=1, le=5, examples=[5])
    comment: str = Field(min_length=3, max_length=2000)


class ReviewReplace(ReviewCreate):
    """Visas atsiliepimo turinys, naudojamas PUT operacijoje."""


class ReviewRead(BaseModel):
    id: int
    build_id: int
    author_name: str
    rating: int
    comment: str
    created_at: datetime
    links: "ReviewLinks"


class ReviewLinks(BaseModel):
    self: str
    build: str
