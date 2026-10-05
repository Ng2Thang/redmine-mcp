"""Internal permission evidence; a positive role permission is never an effective grant."""

from dataclasses import dataclass
from typing import Literal

CapabilityState = Literal["denied", "conditional", "unknown"]
WriteOperation = Literal[
    "upload_attachment",
    "add_project_file",
    "update_attachment",
    "delete_attachment",
    "create_issue",
    "update_issue",
    "update_issue_note",
    "create_issue_relation",
    "delete_issue_relation",
    "add_issue_watcher",
    "remove_issue_watcher",
]


@dataclass(frozen=True)
class MembershipRole:
    role_id: int
    inherited: bool = False


@dataclass(frozen=True)
class ProjectMembership:
    project_id: int
    roles: tuple[MembershipRole, ...]


@dataclass(frozen=True)
class CapabilityProfile:
    user_id: int
    admin: bool | None
    memberships: tuple[ProjectMembership, ...] | None


@dataclass(frozen=True)
class RolePermissions:
    role_id: int
    permissions: frozenset[str]
    issues_visibility: str | None
    time_entries_visibility: str | None
    users_visibility: str | None


@dataclass(frozen=True)
class ProjectInventory:
    project_ids: tuple[int, ...]
    complete: bool


@dataclass(frozen=True)
class WriteIntent:
    operation: WriteOperation
    project_id: int | None = None
    issue_id: int | None = None
    copy_from: int | None = None
    journal_id: int | None = None
    relation_id: int | None = None
    attachment_id: int | None = None
    container_type: Literal["project", "version", "issue"] | None = None
    container_id: int | None = None


@dataclass(frozen=True)
class PermissionClause:
    project_id: int | None
    alternatives: frozenset[str]


@dataclass(frozen=True)
class PermissionExpression:
    """OR of branches, each branch an AND of necessary clauses."""

    branches: tuple[tuple[PermissionClause, ...], ...]
