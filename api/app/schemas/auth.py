from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.auth import Role
from app.schemas.common import ApiInput


class Credentials(ApiInput):
    # Password whitespace is significant; normalize only the username.
    model_config = ConfigDict(str_strip_whitespace=False)
    username: str = Field(min_length=3, max_length=80, pattern=r"^[a-zA-Z0-9_.-]+$")
    password: str = Field(min_length=8, max_length=128)

    @field_validator("username", mode="before")
    @classmethod
    def normalize_username(cls, value):
        return value.strip().lower() if isinstance(value, str) else value


class RefreshInput(ApiInput):
    refresh_token: str = Field(min_length=1, max_length=512)


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    username: str
    role: Role


class RoleUpdate(ApiInput):
    role: Role


class UserPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    username: str


class UserAdminRead(UserRead):
    is_blocked: bool


class UserStatusUpdate(ApiInput):
    is_blocked: bool
