"""Public Redmine adapters used by dependency composition."""

from redmine_mcp.integrations.redmine.attachment_updates import RedmineAttachmentUpdates
from redmine_mcp.integrations.redmine.attachments import RedmineAttachments
from redmine_mcp.integrations.redmine.client import RedmineClient
from redmine_mcp.integrations.redmine.identity import RedmineIdentity
from redmine_mcp.integrations.redmine.issues import RedmineIssues
from redmine_mcp.integrations.redmine.policy import ReadPolicy
from redmine_mcp.integrations.redmine.project_files import RedmineProjectFiles
from redmine_mcp.integrations.redmine.projects import RedmineProjects
from redmine_mcp.integrations.redmine.reference_data import RedmineReferenceData
from redmine_mcp.integrations.redmine.time_entries import RedmineTimeEntries
from redmine_mcp.integrations.redmine.transport import create_upstream_client
from redmine_mcp.integrations.redmine.uploads import RedmineUploads
from redmine_mcp.integrations.redmine.users import RedmineUsers
from redmine_mcp.integrations.redmine.write import RedmineWriter, WriteReceipt

__all__ = [
    "ReadPolicy",
    "RedmineAttachments",
    "RedmineAttachmentUpdates",
    "RedmineClient",
    "RedmineIdentity",
    "RedmineIssues",
    "RedmineProjects",
    "RedmineProjectFiles",
    "RedmineReferenceData",
    "RedmineTimeEntries",
    "RedmineUsers",
    "RedmineUploads",
    "RedmineWriter",
    "WriteReceipt",
    "create_upstream_client",
]
