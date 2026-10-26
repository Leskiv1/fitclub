"""Shared building blocks for request and response schemas."""

import re
from typing import Annotated

from pydantic import AfterValidator, BaseModel, ConfigDict, Field

PHONE_RE = re.compile(r"^\+?\d{10,15}$")


def _normalize_phone(value: str) -> str:
    phone = re.sub(r"[\s\-()]", "", value)
    if not PHONE_RE.fullmatch(phone):
        raise ValueError("телефон має містити 10–15 цифр, наприклад +380671234567")
    return phone


Phone = Annotated[str, AfterValidator(_normalize_phone)]
Name = Annotated[str, Field(min_length=2, max_length=150, examples=["Шевченко Тарас"])]
Password = Annotated[str, Field(min_length=6, max_length=128)]


class Schema(BaseModel):
    """Base for all schemas: strips whitespace and reads attributes from ORM objects."""

    model_config = ConfigDict(from_attributes=True, str_strip_whitespace=True)


class Page[ItemT](BaseModel):
    items: list[ItemT]
    total: int
    offset: int
    limit: int


class PageParams(BaseModel):
    offset: int = Field(0, ge=0)
    limit: int = Field(20, ge=1, le=100)
