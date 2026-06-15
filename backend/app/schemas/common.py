"""Common response schemas."""

from pydantic import BaseModel, ConfigDict


class ListResponse[T](BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[T]
    total: int
    offset: int = 0
    limit: int = 100
