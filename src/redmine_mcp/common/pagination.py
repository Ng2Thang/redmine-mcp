from dataclasses import dataclass
from typing import TypeVar

from pydantic import BaseModel, ConfigDict, Field

from redmine_mcp.common.errors import ApplicationError
from redmine_mcp.common.visibility import Visibility

T = TypeVar("T")


class PageRequest(BaseModel):
    model_config = ConfigDict(strict=True, frozen=True, extra="forbid")

    limit: int = Field(default=25, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


class PaginationPolicy(BaseModel):
    total_pages: int = Field(ge=0)
    max_query_pages: int = Field(ge=1)
    requires_narrowing: bool


@dataclass(frozen=True)
class PaginationGuard:
    max_pages: int = 10

    def check_depth(self, limit: int, offset: int, guidance: str) -> None:
        if offset + limit > self.max_pages * limit:
            raise ApplicationError("scope_required", guidance, 422)

    def describe(self, total: int, limit: int) -> PaginationPolicy:
        pages = (total + limit - 1) // limit
        return PaginationPolicy(
            total_pages=pages,
            max_query_pages=self.max_pages,
            requires_narrowing=pages > self.max_pages,
        )

    def require_scope(self, total: int, limit: int, guidance: str) -> None:
        if self.describe(total, limit).requires_narrowing:
            raise ApplicationError("scope_required", guidance, 422)


class Page[T](BaseModel):
    items: list[T]
    total: int
    limit: int
    offset: int
    visibility: Visibility = Field(default_factory=Visibility)
    pagination_policy: PaginationPolicy | None = Field(
        default=None, exclude_if=lambda value: value is None
    )
