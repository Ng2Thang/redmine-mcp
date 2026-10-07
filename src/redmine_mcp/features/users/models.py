from pydantic import BaseModel, Field, StrictBool

from redmine_mcp.common import PositiveID, Visibility


class UserReference(BaseModel):
    id: PositiveID
    name: str = Field(min_length=1)


class MembershipRole(UserReference):
    inherited: StrictBool = False


class UserMembership(BaseModel):
    id: PositiveID
    project: UserReference
    roles: list[MembershipRole]


class CurrentUser(BaseModel):
    id: PositiveID
    login: str = Field(min_length=1)
    firstname: str
    lastname: str
    mail: str | None = None
    memberships: list[UserMembership]
    visibility: Visibility = Field(default_factory=Visibility)
