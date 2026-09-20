from math import isfinite
from typing import Any

from pydantic import BaseModel, ConfigDict, model_validator


class ApiInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, allow_inf_nan=False, extra="forbid")

    @model_validator(mode="before")
    @classmethod
    def validate_database_values(cls, value: Any) -> Any:
        """Reject values that JSON can parse but PostgreSQL cannot store."""

        def validate(item: Any) -> None:
            if isinstance(item, str):
                if "\x00" in item:
                    raise ValueError("Tekste negali būti nulinio simbolio.")
                try:
                    item.encode("utf-8")
                except UnicodeEncodeError as exc:
                    raise ValueError("Tekstas turi būti tinkamas UTF-8.") from exc
            elif isinstance(item, float) and not isfinite(item):
                raise ValueError("Skaičius turi būti baigtinis.")
            elif isinstance(item, dict):
                for key, child in item.items():
                    validate(key)
                    validate(child)
            elif isinstance(item, list):
                for child in item:
                    validate(child)

        validate(value)
        return value


class ErrorResponse(BaseModel):
    detail: str
