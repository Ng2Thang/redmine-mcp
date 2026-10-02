from typing import Literal

from pydantic import AwareDatetime, Field, model_validator

from redmine_mcp.common import InvalidInputError, PageRequest
from redmine_mcp.constants import issues as issues_text
from redmine_mcp.features.issues.models import ISSUE_INCLUDES, ISSUE_LIST_INCLUDES

IssueSort = Literal["id:asc", "id:desc", "updated_on:asc", "updated_on:desc"]


class IssueSearch(PageRequest):
    project_id: int | None = Field(default=None, gt=0)
    status_id: str = Field(default="open", pattern=r"^(open|closed|\*|[1-9][0-9]*)$")
    assigned_to_id: str | None = Field(default=None, pattern=r"^(me|[1-9][0-9]*)$")
    tracker_id: int | None = Field(default=None, gt=0)
    parent_id: int | None = Field(default=None, gt=0)
    updated_since: AwareDatetime | None = None
    sort: IssueSort = "id:asc"
    category_id: int | None = Field(default=None, gt=0)
    fixed_version_id: int | None = Field(default=None, gt=0)
    include_subprojects: bool = True

    @model_validator(mode="after")
    def require_project_scope(self) -> "IssueSearch":
        if self.category_id is not None and self.project_id is None:
            raise InvalidInputError(issues_text.PROJECT_REQUIRED_FOR_CATEGORY)
        if not self.include_subprojects and self.project_id is None:
            raise InvalidInputError(issues_text.PROJECT_REQUIRED_WITHOUT_SUBPROJECTS)
        return self


def validate_issue_includes(include: tuple[str, ...] | None) -> tuple[str, ...] | None:
    if include is None:
        return None
    if (
        not isinstance(include, tuple)
        or any(not isinstance(part, str) or part not in ISSUE_INCLUDES for part in include)
        or len(set(include)) != len(include)
    ):
        raise InvalidInputError(issues_text.INVALID_INCLUDE_SELECTION)
    return include


def validate_issue_list_includes(include: tuple[str, ...] | None) -> tuple[str, ...] | None:
    if include is None:
        return None
    if (
        not isinstance(include, tuple)
        or not include
        or any(not isinstance(part, str) or part not in ISSUE_LIST_INCLUDES for part in include)
        or len(set(include)) != len(include)
    ):
        raise InvalidInputError(issues_text.INVALID_INCLUDE_SELECTION)
    return include
