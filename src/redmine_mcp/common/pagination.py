from typing import TypeVar

from pydantic import BaseModel, Field

from redmine_mcp.common.visibility import Visibility

T = TypeVar("T")


class Page[T](BaseModel):
    items: list[T]
    total: int
    limit: int
    offset: int
    visibility: Visibility = Field(default_factory=Visibility)
