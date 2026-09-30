from typing import Literal

from pydantic import BaseModel, Field

from redmine_mcp.common.visibility import Visibility


class Reference(BaseModel):
    id: int
    name: str


class Project(BaseModel):
    id: int
    identifier: str
    name: str
    description: str | None = None
    status: int
    parent: Reference | None = None


class ProjectDetail(Project):
    is_public: bool | None = None
    created_on: str | None = None
    updated_on: str | None = None
    visibility: Visibility = Field(default_factory=Visibility)


class Version(BaseModel):
    id: int = Field(gt=0)
    name: str = Field(min_length=1)
    project: Reference
    status: Literal["open", "locked", "closed"]
    description: str | None = None
    due_date: str | None = None


class IssueCategory(BaseModel):
    id: int = Field(gt=0)
    name: str = Field(min_length=1)
    project: Reference
    assigned_to: Reference | None = None
