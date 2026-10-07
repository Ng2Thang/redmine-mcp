"""Native membership APIs; bounded proofs and single-attempt writes."""

import asyncio
from typing import Any

from fastapi import status as http_status
from pydantic import ValidationError

from redmine_mcp.common import ApplicationError, Page
from redmine_mcp.common.read_budget import check_read_deadline
from redmine_mcp.constants import codes as codes_text
from redmine_mcp.features.projects.membership_models import (
    MembershipAction,
    MembershipError,
    MembershipReference,
    MembershipRole,
    MembershipWriteResult,
    ProjectMembership,
    normalize_membership_roles,
)
from redmine_mcp.integrations.redmine.client import RedmineClient
from redmine_mcp.integrations.redmine.responses import (
    resource_object,
    response_items,
    response_object,
    response_page,
)
from redmine_mcp.integrations.redmine.write import RedmineWriter, RedmineWriteRejected, WriteReceipt


def malformed() -> ApplicationError:
    return ApplicationError(
        codes_text.UPSTREAM_RESPONSE,
        "Invalid Redmine membership response",
        http_status.HTTP_502_BAD_GATEWAY,
    )


def member_model(value: Any) -> ProjectMembership:
    try:
        return ProjectMembership.model_validate(value)
    except ValidationError:
        raise malformed() from None


class RedmineProjectMemberships:
    def __init__(self, client: RedmineClient, writer: RedmineWriter) -> None:
        self.client = client
        self.writer = writer
        self._users: dict[int, dict[str, Any]] = {}

    async def list_members(
        self, project_id: int, limit: int, offset: int
    ) -> Page[ProjectMembership]:
        data = await self.client.get_page(
            f"projects/{project_id}/memberships.json",
            "memberships",
            {"limit": limit, "offset": offset},
            "Project membership page budget exceeded; reduce scope or use Redmine directly",
            require_metadata=True,
        )
        page = response_page(data, "memberships", limit, offset, require_metadata=True)
        members = [member_model(value) for value in page.items]
        if any(member.project.id != project_id for member in members):
            raise malformed()
        if len({member.id for member in members}) != len(members):
            raise malformed()
        return Page[ProjectMembership](
            items=members,
            total=page.total,
            limit=limit,
            offset=offset,
            pagination_policy=self.client.pagination.describe(page.total, limit),
        )

    async def membership(self, membership_id: int) -> ProjectMembership:
        data = await self.client.get(f"memberships/{membership_id}.json", {})
        return member_model(resource_object(data.get("membership"), membership_id))

    async def prove_project(self, project_id: int) -> None:
        data = await self.client.get(f"projects/{project_id}.json", {})
        resource_object(data.get("project"), project_id)

    async def prove_user(self, user_id: int) -> None:
        data = await self.client.get(f"users/{user_id}.json", {"include": "memberships"})
        self._users[user_id] = resource_object(data.get("user"), user_id)

    async def role_ids(self) -> set[int]:
        data = await self.client.get("roles.json", {})
        ids: set[int] = set()
        for role in response_items(data, "roles"):
            role_id = role.get("id")
            if type(role_id) is not int or role_id < 1 or role_id in ids:
                raise malformed()
            ids.add(role_id)
        return ids

    async def inventory(self, project_id: int) -> list[ProjectMembership]:
        """Require every page before using absence as evidence. No short-page inference."""
        members: list[ProjectMembership] = []
        expected_total: int | None = None
        seen: set[int] = set()
        for page_number in range(self.client.policy.max_query_pages):
            page = await self.list_members(project_id, 100, page_number * 100)
            if expected_total is None:
                expected_total = page.total
                self.client.pagination.require_scope(
                    page.total, 100, "Complete membership inventory exceeds page budget"
                )
            if page.total != expected_total or any(member.id in seen for member in page.items):
                raise ApplicationError(
                    "membership_inventory_changed",
                    "Membership inventory changed; reconcile",
                    http_status.HTTP_422_UNPROCESSABLE_CONTENT,
                )
            seen.update(member.id for member in page.items)
            members.extend(page.items)
            if len(members) == expected_total:
                return members
            if not page.items or len(members) > expected_total:
                raise malformed()
        raise ApplicationError(
            "scope_required",
            "Complete membership inventory unavailable",
            http_status.HTTP_422_UNPROCESSABLE_CONTENT,
        )

    async def existing(self, project_id: int, user_id: int) -> ProjectMembership | None:
        user = self._users.get(user_id)
        if user is not None and "memberships" in user:
            # The user endpoint returns memberships visible to this caller. Project access
            # was proved separately; no global user listing or administrator credential.
            matches: list[int] = []
            seen: set[int] = set()
            for value in response_items(user, "memberships"):
                project = response_object(value.get("project"))
                try:
                    MembershipReference.model_validate(project)
                    normalize_membership_roles(
                        [
                            MembershipRole.model_validate(role)
                            for role in response_items(value, "roles")
                        ]
                    )
                except ValueError:
                    raise malformed() from None
                project_key, membership_id = project.get("id"), value.get("id")
                if (
                    type(project_key) is not int
                    or project_key < 1
                    or type(membership_id) is not int
                    or membership_id < 1
                    or membership_id in seen
                ):
                    raise malformed()
                seen.add(membership_id)
                if project_key == project_id:
                    matches.append(membership_id)
            if len(matches) > 1:
                raise malformed()
            if not matches:
                return None
            member = await self.membership(matches[0])
            if member.project.id != project_id or member.user is None or member.user.id != user_id:
                raise malformed()
            return member
        # Missing expansion cannot prove absence; use a complete, bounded project inventory.
        matches_members = [
            member
            for member in await self.inventory(project_id)
            if member.user is not None and member.user.id == user_id
        ]
        if len(matches_members) > 1:
            raise malformed()
        return matches_members[0] if matches_members else None

    async def _add(self, result: MembershipWriteResult) -> WriteReceipt | None:
        try:
            return await self.writer.write_json(
                "POST",
                f"projects/{result.project_id}/memberships.json",
                {"membership": {"user_id": result.user_id, "role_ids": result.requested_role_ids}},
                accepted_statuses=(http_status.HTTP_201_CREATED,),
            )
        except RedmineWriteRejected as exc:
            result.outcome = "rejected"
            result.error = MembershipError(code=exc.code, message=exc.message, status=exc.status)
            # A concurrent create can invalidate preflight. Observe, never retry or update.
            try:
                if result.user_id is None:
                    raise malformed()
                await self.prove_user(result.user_id)
                existing = await self.existing(result.project_id, result.user_id)
                if existing is not None:
                    result.membership_id = existing.id
                    result.observed_membership = existing
                    result.observed_present = True
                    result.error = MembershipError(
                        code="membership_already_exists",
                        message="Membership already exists",
                        status=http_status.HTTP_422_UNPROCESSABLE_CONTENT,
                    )
            except ApplicationError as observation_error:
                result.error = MembershipError(
                    code=observation_error.code,
                    message=observation_error.message,
                    status=observation_error.status,
                )
            return None

    async def _dispatch(
        self, action: MembershipAction, result: MembershipWriteResult
    ) -> WriteReceipt | None:
        if action == "add":
            return await self._add(result)
        return await self.writer.write_json(
            "PUT" if action == "update" else "DELETE",
            f"memberships/{result.membership_id}.json",
            {"membership": {"role_ids": result.requested_role_ids}} if action == "update" else None,
            accepted_statuses=(http_status.HTTP_200_OK, http_status.HTTP_204_NO_CONTENT),
            allow_empty_success=True,
        )

    async def write(self, action: MembershipAction, result: MembershipWriteResult) -> None:
        check_read_deadline()
        try:
            receipt = await self._dispatch(action, result)
        except asyncio.CancelledError:
            if result.outcome == "not_executed":
                result.outcome = "uncertain"
                result.error = MembershipError(
                    code="write_interrupted",
                    message="Dispatch interrupted; reconcile before resuming",
                )
            # Do not swallow shutdown/client cancellation or dispatch another item.
            raise
        if receipt is None:
            return
        result.outcome = receipt.outcome
        if receipt.outcome == "uncertain":
            result.error = MembershipError(
                code="write_outcome_uncertain", message="Reconcile before any further attempt"
            )
            return
        try:
            if action == "add":
                created = member_model((receipt.payload or {}).get("membership"))
                result.membership_id = created.id
                if (
                    created.project.id != result.project_id
                    or created.user is None
                    or created.user.id != result.user_id
                ):
                    raise malformed()
            if action == "delete":
                inventory = await self.inventory(result.project_id)
                member = next((m for m in inventory if m.id == result.membership_id), None)
                result.observed_membership = member
                result.observed_present = member is not None
                result.verification = "matched" if member is None else "mismatch"
            else:
                if result.membership_id is None:
                    raise malformed()
                member = await self.membership(result.membership_id)
                if (
                    member.project.id != result.project_id
                    or member.user is None
                    or member.user.id != result.user_id
                ):
                    raise malformed()
                result.observed_membership = member
                result.observed_present = True
                result.verification = (
                    "matched"
                    if {r.id for r in member.roles} == set(result.requested_role_ids or [])
                    else "mismatch"
                )
        except ApplicationError as exc:
            # A failed observation never rewrites an accepted mutation as rejected.
            result.error = MembershipError(code=exc.code, message=exc.message, status=exc.status)
