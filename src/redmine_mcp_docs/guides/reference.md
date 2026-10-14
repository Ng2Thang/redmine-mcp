# Supported tools and capabilities

See what you can do with Redmine MCP, which actions require writer access, and the limits
to expect. Follow [everyday workflows](workflows.md) for examples and copyable prompts.

## Tools by task

The registered catalog contains **36 tools: 18 reads and 18 writes**. The tables below list
every registered operation. Your connection may expose fewer tools: the default reader
exposes reads, while a separate writer adds only the configured write actions. Each caller
uses a personal Redmine API key, and native permissions still apply to the target.

### Read tools (18)

| Tool | What you can do | Scope or limit |
| --- | --- | --- |
| `get_current_user` | Identify the account and its visible project memberships | No arguments; memberships are not a complete permission report |
| `list_my_project_capabilities` | Discover candidate tools and project permissions | Filter by project or operation; conditional or unknown candidates can still fail |
| `list_projects` | Discover visible projects and resolve names to IDs | Paginated; no project-name search argument |
| `get_project` | Read project metadata | One numeric project ID |
| `list_project_members` | Read project memberships, roles, and inheritance | One to ten project IDs; each project has its own page |
| `list_project_versions` | Resolve available Target versions | One project; shared versions may belong to another project |
| `list_project_issue_categories` | Resolve project issue categories | One project; use category IDs with that same project |
| `list_project_files` | List project and version file metadata and links | No file-content download or pagination inputs |
| `list_project_time_entry_activities` | Resolve active activities for logging time | One project; does not identify the caller's default activity |
| `list_issues` | Find issues using supported filters | Open issues by default; supports estimates, dates, and spent-time fields when available |
| `get_issue` | Read an issue, its notes, and selected related data | Journals and attachments by default; other expansions must be requested |
| `get_attachment` | Read attachment metadata and a browser link | One attachment; does not download its content |
| `list_time_entries` | Read logged time across visible projects | Filter by project, credited user, issue, or spent dates; can include project-only entries |
| `list_issue_time_entries` | Read time entries logged directly on an issue | Excludes child issues; has no date filters |
| `list_issue_statuses` | Resolve status IDs and closed flags | Global definitions; use an issue's `allowed_statuses` for its available transitions |
| `list_trackers` | Resolve tracker IDs and standard fields | Global definitions do not prove availability in a project |
| `list_issue_priorities` | Resolve priority IDs and the default priority | Global definitions; `list_issues` has no priority filter |
| `list_document_categories` | Resolve document category IDs and defaults | Global definitions; does not read project documents |

### Write tools (18)

All writes require an enabled writer, configured operations, and the caller's native Redmine
permissions. There is no separate writer key hash or user ID admission list.

| Tool | What you can do | Scope or limit |
| --- | --- | --- |
| `create_issue` | Create an issue or copy one visible source issue | Requires a destination project; copying does not copy the source subtree |
| `update_issue` | Change supplied fields, attach uploads, or add a note | One issue; omitted fields are preserved and native workflow rules apply |
| `update_issue_note` | Edit an existing note or its privacy | Requires issue and journal IDs; clearing text does not delete the journal record |
| `create_issue_relation` | Link two visible issues | One relation; scheduling relations can change dates |
| `delete_issue_relation` | Remove an existing relation | One relation ID; does not restore dates changed by scheduling |
| `add_issue_watcher` | Add a watcher to an issue | One principal; acceptance alone does not prove it was added |
| `remove_issue_watcher` | Remove a direct watcher entry | One principal; watching through a group can remain |
| `create_time_entry` | Log the caller's own time | One visible issue, positive hours, and an explicit date |
| `update_time_entry` | Correct hours, date, activity, or comments | One entry on the declared issue; cannot move it or change the credited user |
| `delete_time_entry` | Permanently remove a selected time entry | One entry on the declared issue; no undo |
| `upload_attachment` | Upload base64 content and obtain a temporary token | The upload remains unattached until a later attach operation |
| `add_project_file` | Attach an upload token as a project file | An optional version must belong to the selected project |
| `update_attachment` | Change an attachment's filename or description | Must identify its project, version, or issue container |
| `delete_attachment` | Delete a selected attachment | Must identify its container; deletion can remove stored bytes |
| `create_project_version` | Create a Target version | Creates an open, unshared version; does not update an existing one |
| `add_project_members` | Add user memberships and roles | One to ten items; existing memberships are rejected |
| `update_project_members` | Set roles on user memberships | One to ten items; native inherited and protected roles are preserved |
| `delete_project_members` | Remove eligible user memberships | One to ten items; groups and inherited memberships are rejected |

An upload token can be attached with `add_project_file` or with the `uploads` input on
`create_issue` or `update_issue`. Uploading alone does not attach a file to an issue or project.
Membership batches perform preflight before writes, but are not atomic transactions.
For every writer, acceptance and independent verification are separate. Inspect each receipt
and reconcile uncertain results before retrying; see [write actions](write-actions.md).

The [full tool reference](../docs/tool-reference.md#tools-and-inputs) lists REST endpoints,
inputs, and receipt contracts. Your server's MCP schemas and REST OpenAPI at `/docs` supply
exact accepted arguments.

## Issue filters and reporting

`list_issues` supports project, category, Target version, status, assignee, tracker, parent,
last-update time, and known tag names. Use `status_id: "*"` to include closed issues and
`assigned_to_id: "me"` to select your own assignments. Resolve names to IDs with the readers
above. Category filtering requires a project. Subproject inclusion defaults to true for issue
queries and false for time-entry queries with a project filter.

`tags_any` matches any of the supplied known names and combines with the other issue filters.
It depends on the existing Redmine server's native tag-filter support. Assigned tags appear
on `get_issue` only when Redmine supplies them; filtering does not provide a complete tag list.

Time-report dates filter the entry's `spent_on`, not the issue's schedule. Reports can group
visible entries by project, credited user, activity, or day. Totals are calculated by the
client after complete permitted pagination; there is no separate report-generation tool.
Do not sum overlapping issue-and-child totals or treat unavailable estimates as zero.
See [time reports](time-report.md) for a walkthrough.

## Outside the current catalog

- General issue deletion, full-text issue search, and project creation or deletion.
- Direct attachment content downloads through MCP; use the authenticated browser links.
- Document record reads or writes; only document category discovery is available.
- Tag-name discovery or tag creation, assignment, removal, renaming, and merging.
- Project-only time-entry writes, logging another user's time, or bulk time-entry mutations.

These limits describe the registered MCP tools, not every action available in Redmine itself.

## Configuration and operations

| Question | Reference |
| --- | --- |
| Which server settings can I change? | [Runtime configuration](../docs/configuration.md) |
| How do I deploy a writer? | [Writer configuration](../docs/configuration.md#separate-writer-deployment) |
| How do I operate Docker or connect external Redmine? | [Operations](../docs/operations.md) |
| How do issue tags depend on plugins? | [RedmineUP tags](https://github.com/Ng2Thang/redmine-mcp/blob/master/docs/integrations/redmineup-tags.md) |
| How should credentials be handled? | [Security policy](https://github.com/Ng2Thang/redmine-mcp/blob/master/SECURITY.md) |

## Result boundaries

Results are caller-visible. Paginated readers can return a discovery preview; inspect
`pagination_policy` before continuing and narrow the scope when required. Stop on
`scope_required` or `scan_budget_exceeded`, and label incomplete totals as partial or unavailable.
Unpaged catalogs and file lists do not accept pagination arguments. Missing values are
unavailable unless the contract says otherwise.

The target is Redmine 7.0.2 and the implementation is an unreleased pilot. Activity discovery
testing was waived, and time-entry creation testing is pending. Existing evidence, gaps,
and later operation records remain in the [capability roadmap](../docs/plans/index.md).
Guide examples do not add runtime evidence.
