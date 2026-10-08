from datetime import UTC, datetime

from redmine_mcp.common import Page
from redmine_mcp.features.issues import ISSUE_INCLUDES, Issue, IssueDetailWithTags
from redmine_mcp.features.issues.models import ISSUE_LIST_INCLUDES
from redmine_mcp.integrations.redmine.client import RedmineClient
from redmine_mcp.integrations.redmine.mapping import page, visible_item
from redmine_mcp.integrations.redmine.responses import resource_object

ISSUE_HOUR_FIELDS = ("spent_hours", "total_spent_hours")
ISSUE_ESTIMATE_FIELDS = ("estimated_hours", "total_estimated_hours")


class RedmineIssues:
    def __init__(self, client: RedmineClient) -> None:
        self.client = client

    async def list_issues(
        self,
        project_id: int | None,
        status_id: str,
        assigned_to_id: str | None,
        limit: int,
        offset: int,
        tracker_id: int | None,
        parent_id: int | None,
        updated_since: datetime | None,
        sort: str,
        category_id: int | None,
        fixed_version_id: int | None,
        include_subprojects: bool,
        include: tuple[str, ...] | None,
        tags_any: list[str] | None = None,
    ) -> Page[Issue]:
        params: dict[str, str | int | list[str]] = {
            "limit": limit,
            "offset": offset,
            "status_id": status_id,
            "sort": sort,
        }
        if project_id is not None:
            params["project_id"] = project_id
        if category_id is not None:
            params["category_id"] = category_id
        if fixed_version_id is not None:
            params["fixed_version_id"] = fixed_version_id
        if not include_subprojects:
            params["subproject_id"] = "!*"
        if assigned_to_id is not None:
            params["assigned_to_id"] = assigned_to_id
        if tracker_id is not None:
            params["tracker_id"] = tracker_id
        if parent_id is not None:
            params["parent_id"] = parent_id
        if updated_since is not None:
            utc_timestamp = updated_since.astimezone(UTC).isoformat().replace("+00:00", "Z")
            params["updated_on"] = f">={utc_timestamp}"
        if include is not None:
            params["include"] = ",".join(include)
        if tags_any is not None:
            # fields[] selects Redmine's structured branch and replaces short filters.
            fields: list[str] = []
            structured: dict[str, str | int | list[str]] = {"set_filter": 1, "fields[]": fields}

            def add_filter(field: str, operator: str, values: list[str]) -> None:
                fields.append(field)
                structured[f"operators[{field}]"] = operator
                structured[f"values[{field}][]"] = values

            add_filter("issue_tags", "=", list(tags_any))
            status_operator = {"open": "o", "closed": "c", "*": "*"}.get(status_id)
            add_filter("status_id", status_operator or "=", ["" if status_operator else status_id])
            for field in (
                "assigned_to_id",
                "tracker_id",
                "parent_id",
                "category_id",
                "fixed_version_id",
            ):
                value = params.pop(field, None)
                if value is not None:
                    add_filter(field, "=", [str(value)])
            params.pop("status_id")
            if updated_since is not None:
                params.pop("updated_on")
                add_filter("updated_on", ">=", [utc_timestamp])
            if not include_subprojects:
                params.pop("subproject_id")
                add_filter("subproject_id", "!*", [""])
            params.update(structured)
        data = await self.client.get_page(
            "issues.json",
            "issues",
            params,
            "Narrow issue filters: project, status, assignee, tracker, version, category, "
            "parent or updated_since; this query requires too many pages",
        )
        selected = include or ()
        result = page(
            Issue,
            data,
            "issues",
            limit,
            offset,
            observed_fields=(*ISSUE_HOUR_FIELDS, *ISSUE_ESTIMATE_FIELDS),
            requested_fields=selected,
            unrequested_fields=sorted(ISSUE_LIST_INCLUDES.difference(selected)),
        )
        result.pagination_policy = self.client.pagination.describe(result.total, limit)
        return result

    async def get_issue(
        self, issue_id: int, include: tuple[str, ...] | None = None
    ) -> IssueDetailWithTags:
        selected = ("journals", "attachments") if include is None else include
        params: dict[str, str | int] = {"include": ",".join(selected)} if selected else {}
        data = await self.client.get(f"issues/{issue_id}.json", params)
        raw_issue = resource_object(data.get("issue"), issue_id)
        return visible_item(
            IssueDetailWithTags,
            raw_issue,
            observed_fields=(*ISSUE_HOUR_FIELDS, *ISSUE_ESTIMATE_FIELDS, "tags"),
            requested_fields=selected,
            unrequested_fields=sorted(ISSUE_INCLUDES.difference(selected)),
        )
