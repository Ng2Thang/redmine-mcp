# Synthetic data

Bootstrap requires redmine-mcp-synthetic-v1 and refuses unknown nonempty instances.
It sets a dedicated application title; Git Bash helpers also validate the .env marker.

Rails creates default configuration, roles, users and custom fields. Python calls REST
to create four private projects, memberships, 150 issues, comments, transitions, relations
and two attachments. Failed requests stop processing. The manifest becomes complete only
after all operations succeed.

Distribution: 110 main, 20 child, 20 restricted issues. Two accessible-project issues are private.
Expected reader count with status_id=* is 128; this is not an automated permission-test result.
MCP Reader has view_issues, default issue visibility, no private-note permission,
and membership in main/child/empty only.

Vietnamese fixture text intentionally exercises Unicode; documentation remains English.

Artifacts:
- .local/environment.json: environment marker.
- .local/credentials.json: sensitive API keys and configuration IDs.
- .local/manifest.json: progress, IDs, privacy cases, attachment names.
- .local/backups/: sensitive snapshots with credentials.

Completed seeds skip reruns; interrupted seeds require reset rather than resume.
Read IDs from the manifest after reset. Only restore trusted snapshots with matching versions.
Full restore, permission, checksum and failure-recovery validation is deferred.

