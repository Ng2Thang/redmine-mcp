"""Project membership contracts, kept separate from caller membership evidence."""

from typing import Annotated, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from redmine_mcp.auth.capability_models import CapabilityState
from redmine_mcp.common import Page, PageRequest, Visibility

PositiveID = Annotated[int, Field(strict=True, gt=0)]
RoleIDs = Annotated[list[PositiveID], Field(min_length=1)]
MembershipAction = Literal["add", "update", "delete"]


class MembershipReference(BaseModel):
    id: PositiveID
    name: str = Field(min_length=1, strict=True)


class MembershipRole(MembershipReference):
    inherited: bool = Field(default=False, strict=True)


def normalize_membership_roles(roles: list[MembershipRole]) -> list[MembershipRole]:
    """Merge native MemberRole rows, retaining any evidence of inheritance."""
    unique: dict[int, MembershipRole] = {}
    for role in roles:
        previous = unique.get(role.id)
        if previous is None:
            unique[role.id] = role.model_copy()
        else:
            if previous.name != role.name:
                raise ValueError("Conflicting membership role names")
            unique[role.id] = previous.model_copy(
                update={"inherited": previous.inherited or role.inherited}
            )
    return list(unique.values())


class ProjectMembership(BaseModel):
    id: PositiveID
    project: MembershipReference
    user: MembershipReference | None = None
    group: MembershipReference | None = None
    roles: list[MembershipRole]
    visibility: Visibility = Field(default_factory=Visibility)

    @field_validator("roles")
    @classmethod
    def normalize_roles(cls, roles: list[MembershipRole]) -> list[MembershipRole]:
        return normalize_membership_roles(roles)

    @model_validator(mode="after")
    def validate_principal(self) -> Self:
        if (self.user is None) == (self.group is None):
            raise ValueError("Membership must identify exactly one user or group")
        return self


class ListProjectMembersRequest(PageRequest):
    project_ids: list[PositiveID] = Field(min_length=1, max_length=10)

    @model_validator(mode="after")
    def unique_projects(self) -> Self:
        if len(set(self.project_ids)) != len(self.project_ids):
            raise ValueError("Project IDs must be unique")
        return self


class MembershipItem(BaseModel):
    model_config = ConfigDict(extra="forbid")
    project_id: PositiveID


class AddMembershipItem(MembershipItem):
    user_id: PositiveID
    role_ids: RoleIDs

    @model_validator(mode="after")
    def unique_roles(self) -> Self:
        if len(set(self.role_ids)) != len(self.role_ids):
            raise ValueError("Role IDs must be unique")
        return self


class DeleteMembershipItem(MembershipItem):
    membership_id: PositiveID


class UpdateMembershipItem(DeleteMembershipItem):
    role_ids: RoleIDs

    @model_validator(mode="after")
    def unique_roles(self) -> Self:
        if len(set(self.role_ids)) != len(self.role_ids):
            raise ValueError("Role IDs must be unique")
        return self


class MembershipBatch[T: MembershipItem](BaseModel):
    model_config = ConfigDict(extra="forbid")
    items: list[T] = Field(min_length=1, max_length=10)

    @model_validator(mode="after")
    def unique_targets(self) -> Self:
        targets = [
            (item.project_id, item.user_id)
            if isinstance(item, AddMembershipItem)
            else item.membership_id
            for item in self.items
            if isinstance(item, (AddMembershipItem, DeleteMembershipItem))
        ]
        if len(set(targets)) != len(targets):
            raise ValueError("Batch targets must be unique")
        return self


class AddProjectMembersRequest(MembershipBatch[AddMembershipItem]):
    pass


class UpdateProjectMembersRequest(MembershipBatch[UpdateMembershipItem]):
    pass


class DeleteProjectMembersRequest(MembershipBatch[DeleteMembershipItem]):
    pass


class MembershipError(BaseModel):
    code: str
    message: str
    status: int | None = None


class ProjectMembersResult(BaseModel):
    project_id: int
    outcome: Literal["read", "rejected", "not_executed"]
    page: Page[ProjectMembership] | None = None
    error: MembershipError | None = None


class ListProjectMembersResult(BaseModel):
    results: list[ProjectMembersResult]


class MembershipWriteResult(BaseModel):
    index: int
    project_id: int
    membership_id: int | None = None
    user_id: int | None = None
    outcome: Literal["accepted", "rejected", "uncertain", "not_executed"] = "not_executed"
    verification: Literal["matched", "mismatch", "unavailable"] = "unavailable"
    requested_role_ids: list[int] | None = None
    observed_membership: ProjectMembership | None = None
    observed_present: bool | None = None
    permission_state: CapabilityState = "unknown"
    error: MembershipError | None = None


class MembershipBatchResult(BaseModel):
    phase: Literal["preflight_failed", "executed"]
    results: list[MembershipWriteResult]
