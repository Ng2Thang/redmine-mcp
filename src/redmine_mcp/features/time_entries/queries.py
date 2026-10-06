from datetime import date
from typing import Annotated, Literal

from pydantic import Field, model_validator

from redmine_mcp.common import InvalidInputError, PageRequest

TimeEntryUserId = Annotated[int, Field(gt=0)] | Literal["me"]


class TimeEntrySearch(PageRequest):
    project_id: int | None = Field(default=None, gt=0)
    include_subprojects: bool = False
    user_id: TimeEntryUserId | None = None
    issue_id: int | None = Field(default=None, gt=0)
    spent_from: date | None = None
    spent_to: date | None = None

    @model_validator(mode="after")
    def require_valid_scope(self) -> "TimeEntrySearch":
        if self.include_subprojects and self.project_id is None:
            raise InvalidInputError("project_id is required when include_subprojects is true")
        if self.spent_from is not None and self.spent_to is not None:
            if self.spent_from > self.spent_to:
                raise InvalidInputError("spent_from must be on or before spent_to")
        return self
