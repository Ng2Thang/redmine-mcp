from pydantic import BaseModel, Field

from redmine_mcp.features.issues import IssueDate, IssueHours


class CreditedUser(BaseModel):
    id: int = Field(strict=True, gt=0)
    name: str


class IssueTimeEntry(BaseModel):
    id: int = Field(strict=True, gt=0)
    issue_id: int = Field(strict=True, gt=0)
    user: CreditedUser
    hours: IssueHours
    spent_on: IssueDate


class TimeEntryReference(BaseModel):
    id: int = Field(strict=True, gt=0)
    name: str


class TimeEntryIssueReference(BaseModel):
    id: int = Field(strict=True, gt=0)


class TimeEntry(BaseModel):
    id: int = Field(strict=True, gt=0)
    project: TimeEntryReference
    user: CreditedUser
    issue_id: int | None = Field(default=None, strict=True, gt=0)
    hours: IssueHours
    spent_on: IssueDate
    activity: TimeEntryReference | None = None
    comments: str | None = None
