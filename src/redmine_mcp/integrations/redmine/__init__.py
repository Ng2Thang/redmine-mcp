"""Public Redmine adapters used by dependency composition."""

from redmine_mcp.integrations.redmine.client import RedmineClient
from redmine_mcp.integrations.redmine.identity import RedmineIdentity
from redmine_mcp.integrations.redmine.issues import RedmineIssues
from redmine_mcp.integrations.redmine.policy import ReadPolicy
from redmine_mcp.integrations.redmine.projects import RedmineProjects
from redmine_mcp.integrations.redmine.reference_data import RedmineReferenceData
from redmine_mcp.integrations.redmine.time_entries import RedmineTimeEntries
from redmine_mcp.integrations.redmine.transport import create_upstream_client
from redmine_mcp.integrations.redmine.users import RedmineUsers

__all__ = [
    "ReadPolicy",
    "RedmineClient",
    "RedmineIdentity",
    "RedmineIssues",
    "RedmineProjects",
    "RedmineReferenceData",
    "RedmineTimeEntries",
    "RedmineUsers",
    "create_upstream_client",
]
