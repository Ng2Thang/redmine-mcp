"""Public advisory capabilities, never an effective authorization grant."""

from typing import Literal

from pydantic import BaseModel, Field, StrictBool

from redmine_mcp.common import Page, PositiveID


class ToolCapability(BaseModel):
    operation_id: str
    state: Literal["conditional", "unknown"]
    reason: str | None = Field(
        default=None,
        exclude_if=lambda value: value is None,
        description="Explanation included only when include_reasons is true.",
    )


class ProjectRoleCapability(BaseModel):
    id: PositiveID
    name: str | None
    inherited: StrictBool


class ProjectCapability(BaseModel):
    id: PositiveID
    name: str
    roles: list[ProjectRoleCapability]
    permissions: list[str] | None = Field(
        description="Sorted unique union of permissions from readable membership roles."
    )
    permissions_state: Literal["known", "partial", "unknown"] = Field(
        description="Whether all, some, or none of the membership roles could be read."
    )
    membership_state: Literal["known", "unknown"]
    tools: list[ToolCapability]


class MyProjectCapabilities(Page[ProjectCapability]):
    user_id: PositiveID
    global_tools: list[ToolCapability]
