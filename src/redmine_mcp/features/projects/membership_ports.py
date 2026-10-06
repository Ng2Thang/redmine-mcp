from typing import Protocol

from redmine_mcp.auth.capability_models import CapabilityState
from redmine_mcp.common import Page
from redmine_mcp.features.projects.membership_models import (
    MembershipAction,
    MembershipWriteResult,
    ProjectMembership,
)


class MembershipGateway(Protocol):
    async def list_members(
        self, project_id: int, limit: int, offset: int
    ) -> Page[ProjectMembership]: ...

    async def membership(self, membership_id: int) -> ProjectMembership: ...

    async def prove_user(self, user_id: int) -> None: ...

    async def prove_project(self, project_id: int) -> None: ...

    async def role_ids(self) -> set[int]: ...

    async def existing(self, project_id: int, user_id: int) -> ProjectMembership | None: ...

    async def write(self, action: MembershipAction, result: MembershipWriteResult) -> None: ...


class MembershipAuthorizer(Protocol):
    def refresh(self) -> None: ...

    async def project_operation(
        self, operation: str, project_id: int | None
    ) -> CapabilityState: ...
