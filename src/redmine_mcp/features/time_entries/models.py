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
