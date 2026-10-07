from pydantic import BaseModel

from redmine_mcp.common import PositiveID
from redmine_mcp.features.issues import IssueDate, IssueHours


class CreditedUser(BaseModel):
    id: PositiveID
    name: str


class IssueTimeEntry(BaseModel):
    id: PositiveID
    issue_id: PositiveID
    user: CreditedUser
    hours: IssueHours
    spent_on: IssueDate


class TimeEntryReference(BaseModel):
    id: PositiveID
    name: str


class TimeEntryIssueReference(BaseModel):
    id: PositiveID


class TimeEntry(BaseModel):
    id: PositiveID
    project: TimeEntryReference
    user: CreditedUser
    issue_id: PositiveID | None = None
    hours: IssueHours
    spent_on: IssueDate
    activity: TimeEntryReference | None = None
    comments: str | None = None
