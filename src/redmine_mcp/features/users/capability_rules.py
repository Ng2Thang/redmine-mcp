"""Advisory read rules based on the pinned Redmine 7.0.2 source and tool prerequisites."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ReadCapabilityRule:
    # OR between branches, AND between permissions in one branch.
    branches: tuple[frozenset[str], ...]
    constraint: str


ISSUE_READ = ReadCapabilityRule(
    (frozenset({"view_issues"}),),
    "Issue tracking availability, issue visibility and private-issue access are checked "
    "by Redmine on invocation.",
)
ATTACHMENT_READ = ReadCapabilityRule(
    tuple(
        frozenset({permission})
        for permission in (
            "view_issues",
            "view_files",
            "view_documents",
            "view_news",
            "view_messages",
            "view_wiki_pages",
        )
    ),
    "Permission evidence covers a possible container type; the attachment's actual container, "
    "visibility are checked on invocation; file retrieval returns a browser download link.",
)

PROJECT_READ_RULES: dict[str, ReadCapabilityRule] = {
    "list_project_members": ReadCapabilityRule(
        (frozenset(),),
        "Redmine 7.0.2 view_members is public; project access and state are checked on "
        "invocation. Manage members permission is not required for listing.",
    ),
    "get_project": ReadCapabilityRule(
        (frozenset(),),
        "This project was visible to the caller when listed or read; "
        "Redmine rechecks project access and metadata visibility on invocation.",
    ),
    "get_issue": ISSUE_READ,
    "list_issues": ISSUE_READ,
    "list_project_versions": ReadCapabilityRule(
        (frozenset({"view_issues"}),),
        "Issue tracking availability and shared-version visibility are checked on invocation.",
    ),
    "list_project_issue_categories": ReadCapabilityRule(
        (frozenset({"view_issues"}), frozenset({"manage_categories"})),
        "Issue tracking availability and project access are checked on invocation.",
    ),
    "list_project_files": ReadCapabilityRule(
        (frozenset({"view_files"}),),
        "Files module availability and project/version file visibility are checked on invocation.",
    ),
    "list_issue_time_entries": ReadCapabilityRule(
        (frozenset({"view_issues", "view_time_entries"}),),
        "The tool reads the issue first; issue visibility, time tracking availability and "
        "role restrictions on visible time entries are checked on invocation.",
    ),
    "get_attachment": ATTACHMENT_READ,
}
