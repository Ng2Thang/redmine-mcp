from pydantic import BaseModel, Field

from redmine_mcp.features.projects import Reference


class IssueStatus(BaseModel):
    id: int = Field(gt=0)
    name: str = Field(min_length=1)
    is_closed: bool = Field(strict=True)


class Tracker(BaseModel):
    id: int = Field(gt=0)
    name: str = Field(min_length=1)
    description: str | None = None
    default_status: Reference | None = None
    enabled_standard_fields: list[str] = Field(default_factory=list)


class IssuePriority(BaseModel):
    id: int = Field(gt=0)
    name: str = Field(min_length=1)
    is_default: bool = Field(strict=True)


class DocumentCategory(BaseModel):
    id: int = Field(gt=0)
    name: str = Field(min_length=1)
    is_default: bool = Field(strict=True)
