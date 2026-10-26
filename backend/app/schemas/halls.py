from pydantic import Field

from app.schemas.common import Schema


class HallCreate(Schema):
    name: str = Field(min_length=2, max_length=100)
    capacity: int = Field(gt=0, le=1000)


class HallUpdate(Schema):
    name: str | None = Field(None, min_length=2, max_length=100)
    capacity: int | None = Field(None, gt=0, le=1000)


class HallRead(Schema):
    id: int
    name: str
    capacity: int
