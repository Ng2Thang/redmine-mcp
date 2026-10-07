"""Watcher acceptance is independent from visible membership verification."""

from redmine_mcp.common import ApplicationError
from redmine_mcp.constants import codes as codes_text
from redmine_mcp.constants import redmine as redmine_text
from redmine_mcp.features.issues.write_models import IssueWatcherResult
from redmine_mcp.features.projects.models import Reference
from redmine_mcp.integrations.redmine.client import RedmineClient
from redmine_mcp.integrations.redmine.mapping import item
from redmine_mcp.integrations.redmine.responses import resource_object, response_items
from redmine_mcp.integrations.redmine.write import RedmineWriter


class RedmineIssueWatchers:
    def __init__(self, client: RedmineClient, writer: RedmineWriter) -> None:
        self.client = client
        self.writer = writer

    async def remove_issue_watcher(self, issue_id: int, user_id: int) -> IssueWatcherResult:
        data = await self.client.get(f"issues/{issue_id}.json", {})
        resource_object(data.get("issue"), issue_id)
        receipt = await self.writer.write_json(
            "DELETE", f"issues/{issue_id}/watchers/{user_id}.json", accepted_statuses=(204,)
        )
        result = IssueWatcherResult(
            outcome=receipt.outcome,
            upstream_accepted=True if receipt.status == 204 else None,
            issue_id=issue_id,
            user_id=user_id,
        )
        try:
            result.observed_present = await self._watcher_present(issue_id, user_id)
        except ApplicationError:
            return result
        if result.observed_present is not None:
            result.verification = "mismatch" if result.observed_present else "matched"
        return result

    async def _watcher_present(self, issue_id: int, user_id: int) -> bool | None:
        data = await self.client.get(f"issues/{issue_id}.json", {"include": "watchers"})
        issue = resource_object(data.get("issue"), issue_id)
        if "watchers" not in issue:
            return None
        seen: set[int] = set()
        for watcher in response_items(issue, "watchers"):
            watcher_id = item(Reference, watcher).id
            if watcher_id in seen:
                raise ApplicationError(
                    codes_text.UPSTREAM_RESPONSE, redmine_text.UNEXPECTED_DATA, 502
                )
            seen.add(watcher_id)
        return user_id in seen

    async def add_issue_watcher(self, issue_id: int, user_id: int) -> IssueWatcherResult:
        data = await self.client.get(f"issues/{issue_id}.json", {})
        resource_object(data.get("issue"), issue_id)
        receipt = await self.writer.write_json(
            "POST",
            f"issues/{issue_id}/watchers.json",
            {"watcher": {"user_id": user_id}},
            accepted_statuses=(204,),
        )
        result = IssueWatcherResult(
            outcome=receipt.outcome,
            upstream_accepted=True if receipt.status == 204 else None,
            issue_id=issue_id,
            user_id=user_id,
        )
        try:
            result.observed_present = await self._watcher_present(issue_id, user_id)
        except ApplicationError:
            return result
        if result.observed_present is not None:
            result.verification = "matched" if result.observed_present else "mismatch"
        return result
