import re
from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from redmine_mcp.common import Visibility


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


class CreateProjectVersionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=60)
    description: str | None = Field(default=None, max_length=255)
    due_date: date | None = None

    @field_validator("name")
    @classmethod
    def require_nonblank_name(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Version name must not be blank")
        return value

    @field_validator("due_date", mode="before")
    @classmethod
    def require_iso_date(cls, value: object) -> object:
        if value is not None and (
            not isinstance(value, str) or not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", value)
        ):
            raise ValueError("Due date must be a calendar date in YYYY-MM-DD format")
        return value


class ProjectVersionObservation(Version):
    sharing: Literal["none", "descendants", "hierarchy", "tree", "system"]


class ProjectVersionError(BaseModel):
    code: Literal["version_already_exists"] = "version_already_exists"
    message: str = (
        "Creation was rejected; a version with this name already exists. "
        "The existing version is returned. Supplied fields were not applied."
    )


class CreateProjectVersionResult(BaseModel):
    outcome: Literal["accepted", "existing", "uncertain"]
    upstream_accepted: bool | None
    resource_id: int | None = Field(default=None, strict=True, gt=0)
    verification: Literal["matched", "mismatch", "unavailable"] = "unavailable"
    observed_version: ProjectVersionObservation | None = None
    error: ProjectVersionError | None = None


class IssueCategory(BaseModel):
    id: int = Field(gt=0)
    name: str = Field(min_length=1)
    project: Reference
    assigned_to: Reference | None = None


class ProjectFile(BaseModel):
    id: int = Field(gt=0)
    filename: str = Field(min_length=1)
    filesize: int = Field(ge=0)
    content_type: str | None = None
    description: str | None = None
    content_url: str
    created_on: str
    author: Reference | None = None
    version: Reference | None = None
    digest: str
    downloads: int = Field(ge=0)


class AddProjectFileRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    token: str = Field(min_length=3, max_length=200)
    filename: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=255)
    version_id: int | None = Field(default=None, strict=True, gt=0)


class AddProjectFileResult(BaseModel):
    outcome: Literal["accepted", "uncertain"]
    upstream_accepted: bool | None
    verification: Literal["matched", "mismatch", "unavailable"] = "unavailable"
    attachment_id: int = Field(gt=0)
    observed_file: ProjectFile | None = None
