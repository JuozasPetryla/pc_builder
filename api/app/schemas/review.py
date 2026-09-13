from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ReviewCreate(BaseModel):
    author_name: str = Field(min_length=2, max_length=80, examples=["Mantas"])
    rating: int = Field(ge=1, le=5, examples=[5])
    comment: str = Field(min_length=3, max_length=2000)


class ReviewRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    build_id: int
    author_name: str
    rating: int
    comment: str
    created_at: datetime
