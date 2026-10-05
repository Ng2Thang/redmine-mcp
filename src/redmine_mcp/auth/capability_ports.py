from typing import Protocol

from redmine_mcp.auth.capability_models import (
    CapabilityProfile,
    PermissionExpression,
    ProjectInventory,
    RolePermissions,
    WriteIntent,
)


class CapabilityReader(Protocol):
    async def profile(self) -> CapabilityProfile: ...

    async def role(self, role_id: int) -> RolePermissions | None: ...

    async def resolve(self, intent: WriteIntent, user_id: int) -> PermissionExpression: ...

    async def visible_projects(self) -> ProjectInventory: ...


class WriteAuthorizer(Protocol):
    async def authorize(self, intent: WriteIntent) -> None: ...
