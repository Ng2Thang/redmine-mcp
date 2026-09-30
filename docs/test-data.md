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

## Optional three-month history

Run `bash scripts/seed-history.sh` after the base seed to add a larger manual-testing fixture.
It requires the same marked synthetic environment and does not alter the original records.
The command adds two parent projects and six subprojects, 20 users, 12 versions used as sprints,
300 issues, and 900 time entries. Seven new projects are visible to MCP Reader; the eighth,
`History Beta Private`, is restricted. Each parent owns six 15-day versions shared with its
subprojects. Issue schedules and time-entry work dates cover the 90 days before the command's
first run, using the seed container's UTC date. Record creation timestamps remain current.

The ignored `.local/history-manifest.json` records the date anchor, generated IDs, progress,
and completion status. A completed command skips reruns. An interrupted run resumes and
reconciles records created just before a checkpoint. A synthetic reset removes this manifest;
backups and restores include it when present. Do not edit it by hand.

For examples, read `projects.alpha-api`, `projects.beta-private`, `versions.alpha:01`,
`issues.001`, and `time_entries.001-1` from the history manifest. IDs change after a reset.
The base manifest's 128 visible issues remain; the expanded fixture adds 263 visible issues,
for 391 total visible issues with `status_id="*"` when no other manual changes have been made.
The restricted project contains 37 of the new issues. Time entries can be checked in Redmine's
Spent time pages; current MCP tools do not expose them.

