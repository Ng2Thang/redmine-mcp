from typing import TypeVar

from pydantic import BaseModel, ConfigDict, Field

from redmine_mcp.common.visibility import Visibility

T = TypeVar("T")


class PageRequest(BaseModel):
    model_config = ConfigDict(strict=True, frozen=True, extra="forbid")

    limit: int = Field(default=25, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


class Page[T](BaseModel):
    items: list[T]
    total: int
    limit: int
    offset: int
    visibility: Visibility = Field(default_factory=Visibility)
