from pydantic import BaseModel, Field, StrictBool

from redmine_mcp.common import PositiveID
from redmine_mcp.features.projects import Reference


class IssueStatus(BaseModel):
    id: PositiveID
    name: str = Field(min_length=1)
    is_closed: StrictBool


class Tracker(BaseModel):
    id: PositiveID
    name: str = Field(min_length=1)
    description: str | None = None
    default_status: Reference | None = None
    enabled_standard_fields: list[str] = Field(default_factory=list)


class IssuePriority(BaseModel):
    id: PositiveID
    name: str = Field(min_length=1)
    is_default: StrictBool


class DocumentCategory(BaseModel):
    id: PositiveID
    name: str = Field(min_length=1)
    is_default: StrictBool
