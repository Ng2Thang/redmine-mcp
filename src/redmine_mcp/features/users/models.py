from pydantic import BaseModel, Field

from redmine_mcp.common import Visibility


class UserReference(BaseModel):
    id: int = Field(gt=0, strict=True)
    name: str = Field(min_length=1)


class MembershipRole(UserReference):
    inherited: bool = Field(default=False, strict=True)


class UserMembership(BaseModel):
    id: int = Field(gt=0, strict=True)
    project: UserReference
    roles: list[MembershipRole]


class CurrentUser(BaseModel):
    id: int = Field(gt=0, strict=True)
    login: str = Field(min_length=1)
    firstname: str
    lastname: str
    mail: str | None = None
    memberships: list[UserMembership]
    visibility: Visibility = Field(default_factory=Visibility)
