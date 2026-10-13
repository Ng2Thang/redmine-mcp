"""Explicit public tool arguments for catalog-wide boundary and safety scenarios."""

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ToolCase:
    operation: str
    arguments: dict[str, Any] = field(default_factory=dict)
    invalid: dict[str, Any] | None = None


# Keep this inventory explicit: a newly registered tool must acquire a reviewed case.
CATALOG_CASES = (
    ToolCase("get_current_user"),
    ToolCase("list_my_project_capabilities", {"project_id": 7}, {"limit": 0}),
    ToolCase("list_projects", {}, {"limit": 0}),
    ToolCase("get_project", {"project_id": 7}, {"project_id": 0}),
    ToolCase("list_project_versions", {"project_id": 7}, {"project_id": 0}),
    ToolCase("list_project_issue_categories", {"project_id": 7}, {"project_id": 0}),
    ToolCase("list_project_files", {"project_id": 7}, {"project_id": 0}),
    ToolCase("list_project_time_entry_activities", {"project_id": 7}, {"project_id": 0}),
    ToolCase("list_project_members", {"project_ids": [7]}, {"project_ids": [0]}),
    ToolCase("list_issues", {"project_id": 7}, {"limit": 0}),
    ToolCase("get_issue", {"issue_id": 42}, {"issue_id": 0}),
    ToolCase("get_attachment", {"attachment_id": 9}, {"attachment_id": 0}),
    ToolCase("list_issue_time_entries", {"issue_id": 42}, {"issue_id": 0}),
    ToolCase("list_time_entries", {"project_id": 7, "user_id": "me"}, {"limit": 0}),
    ToolCase("list_issue_statuses"),
    ToolCase("list_issue_priorities"),
    ToolCase("list_document_categories"),
    ToolCase("list_trackers"),
    ToolCase(
        "create_time_entry",
        {"issue_id": 42, "hours": 1.5, "spent_on": "2026-10-01"},
        {"hours": 0},
    ),
    ToolCase("update_time_entry", {"issue_id": 42, "time_entry_id": 1, "hours": 1}, {"hours": 0}),
    ToolCase("delete_time_entry", {"issue_id": 42, "time_entry_id": 1}, {"time_entry_id": 0}),
    ToolCase(
        "upload_attachment",
        {"filename": "sample.txt", "content_base64": "eA=="},
        {"content_base64": "!"},
    ),
    ToolCase(
        "add_project_file",
        {"project_id": 7, "token": "9.abc", "filename": "sample.txt"},
        {"filename": "../bad.txt"},
    ),
    ToolCase("create_project_version", {"project_id": 7, "name": "sprint"}, {"name": ""}),
    ToolCase(
        "add_project_members",
        {"items": [{"project_id": 7, "user_id": 12, "role_ids": [4]}]},
        {"items": []},
    ),
    ToolCase(
        "update_project_members",
        {"items": [{"project_id": 7, "membership_id": 20, "role_ids": [4]}]},
        {"items": []},
    ),
    ToolCase(
        "delete_project_members",
        {"items": [{"project_id": 7, "membership_id": 20}]},
        {"items": []},
    ),
    ToolCase(
        "update_attachment",
        {"attachment_id": 9, "container_type": "project", "container_id": 7, "description": "new"},
        {"container_id": 0},
    ),
    ToolCase(
        "delete_attachment",
        {"attachment_id": 9, "container_type": "project", "container_id": 7},
        {"container_id": 0},
    ),
    ToolCase("create_issue", {"project_id": 7, "subject": "created"}, {"project_id": 0}),
    ToolCase("update_issue", {"issue_id": 42, "subject": "new"}, {"issue_id": 0}),
    ToolCase(
        "update_issue_note", {"issue_id": 42, "journal_id": 1, "notes": "new"}, {"journal_id": 0}
    ),
    ToolCase("create_issue_relation", {"issue_id": 42, "issue_to_id": 43}, {"issue_to_id": 0}),
    ToolCase("delete_issue_relation", {"relation_id": 1}, {"relation_id": 0}),
    ToolCase("add_issue_watcher", {"issue_id": 42, "user_id": 3}, {"user_id": 0}),
    ToolCase("remove_issue_watcher", {"issue_id": 42, "user_id": 3}, {"user_id": 0}),
)
