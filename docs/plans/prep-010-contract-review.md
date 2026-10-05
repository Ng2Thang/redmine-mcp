# prep-010 permission and session contract review

Reviewed 2026-10-05 against the verified Redmine 7.0.2 release archive (SHA-256
`d45e6d4c373cc3c8d33f1f4d4a2ffae1e1adb18703160707467493de7b4be591`), the current
repository, FastAPI-MCP 0.4.0, and locked MCP SDK 1.30.0. No target runtime executed.
The [official archive](https://www.redmine.org/releases/redmine-7.0.2.tar.gz) is the upstream
source; `.local/upgrades/source/redmine-7.0.2.tar.gz` was inspected without extracting to Git.

## Permission expressions and context ownership

Expressions below are necessary permission gates, never proof of effective access. OR means
any applicable branch may pass; AND combines separate requirements. Unknown metadata must not
be converted into denial. Context is resolved by a typed authorization port/gateway before
mutation; existing gateway membership and payload checks still run. Same-key reads may be
duplicated initially; only request-local capability/role reads are deduplicated.

| Operation | Target context and necessary expression | Exact source |
|---|---|---|
| `upload_attachment` | Global upload: any role path permitting attachments/upload; no target project argument | `attachments_controller.rb:30,104`; `application_controller.rb:339-358`; `lib/redmine/preparation.rb` upload mappings |
| `add_project_file` | Selected project: `manage_files`; existing version association validation retained | `files_controller.rb:23-25,52`; `lib/redmine/preparation.rb:121` |
| `update_attachment` | Prove attachment in declared container; Project/Version: `manage_files`; Issue: `edit_issues` OR (`edit_own_issues` AND issue author is caller) | `attachments_controller.rb:287`; `attachment.rb:213`; `project.rb:68-70`; `version.rb:130-132`; `issue.rb:216-228` |
| `delete_attachment` | Same container proof and expression as attachment update | `attachments_controller.rb:291`; `attachment.rb:221`; `issue.rb:242-243` |
| `create_issue` | Destination `add_issues` AND source `copy_issues` when copy_from exists; read actual source project | `issues_controller.rb:151-153,592-600`; `lib/redmine/preparation.rb:67,70` |
| `update_issue` | Read existing issue: route gate is `edit_issues` OR applicable `edit_own_issues` OR `add_issue_notes`; resolve a supplied destination separately and delegate exact move/field rules | `lib/redmine/preparation.rb:68-75`; `issue.rb:507-548,574-656`; `issues_controller.rb:198,561` |
| `update_issue_note` | Journal must belong to declared issue; `edit_issue_notes` OR (`edit_own_issue_notes` AND journal author is caller) | `journals_controller.rb:86-103`; `journal.rb:150-151`; `lib/redmine/preparation.rb:76-77` |
| `create_issue_relation` | Source project `manage_issue_relations`; read both issues to preserve visibility; target eligibility/cross-project settings stay upstream | `issue_relations_controller.rb:23,46`; `issue_relation.rb:122-127`; `lib/redmine/preparation.rb:71` |
| `delete_issue_relation` | Read relation and actual endpoint issues: source project `manage_issue_relations` OR target project `manage_issue_relations`; both visibility conditions still upstream | `issue_relations_controller.rb:84-85`; `issue_relation.rb:107-110` |
| `add_issue_watcher` | Read actual issue project: `add_issue_watchers`; eligibility and no-op handling stay upstream | `watchers_controller.rb:43-57,238-243`; `lib/redmine/preparation.rb:83` |
| `remove_issue_watcher` | Read actual issue project: `delete_issue_watchers`; group/direct distinctions stay upstream | `watchers_controller.rb:82-96,238-243`; `lib/redmine/preparation.rb:84` |

Global upload candidates include `add_issues`, `edit_issues`, `edit_own_issues`, `copy_issues`,
`add_issue_notes`, `manage_news`, `add_documents`, `edit_documents`, `manage_files`,
`edit_wiki_pages`, `add_messages`, `edit_messages`, and `edit_own_messages`. Do not invent
an `upload` permission. Built-in/non-member/global coverage can remain unknown.

For issue update, do not impose an Edit issues requirement on a notes-only request. Nor may a
mixed request be denied just because one supplied field is not editable: Redmine can apply
permitted notes/fields and ignore other fields, already represented by verification receipts.
Privacy, subtasks, move conditions, destination tracker/workflow and journal privacy stay
authoritative upstream. A locally absent necessary route permission can deny before mutation.

Profile evidence is read via current-user memberships and own `admin` flag. Role JSON is
validated against the requested role ID. A project with explicit memberships can use the
permission union for necessary gates, but each role retains its visibility attributes; no local
visibility grant is derived by combining constraints from different roles. Positive permission
is conditional because tracker restriction data is absent from role JSON. Unknown admin flag,
missing project membership, missing role metadata, and public non-member overrides remain unknown.

Discovery may prove denial across all candidate projects only when its visible-project inventory
is complete and every target has explicit complete role evidence. Enumerate `projects.json` in
pages of 100, deduplicate IDs, require stable total count and progress, and stop after 100 pages.
An incomplete inventory remains unknown; it does not hide possibly available writes. A visible
project without caller membership keeps coverage unknown. No positive metadata cache spans requests.
This also permits useful filtering for callers whose visible projects are all explicit memberships.
Malformed project pagination is an upstream-response error rather than evidence of no projects.

## Session integration at locked versions

SDK `StreamableHTTPSessionManager._handle_stateful_request` already reads an
`AuthenticatedUser` from ASGI `scope["user"]` and compares its `authorization_context` with the
session owner. The SDK owns creation, GET/POST/DELETE lookup, removal on DELETE/termination,
idle expiry and lifespan cleanup. No extra session dictionary or private owner-map patch is needed.

`require_mcp_access` authenticates every request through the existing FastAPI dependency, stores
its private AuthContext in request state, and places an SDK `AuthenticatedUser` in the scope.
Its synthetic AccessToken contains no raw credential: `client_id` is caller user ID, `subject`
is the private SHA-256 fingerprint of the normalized caller key, and issuer is the configured
Redmine URL. This is internal session identity adaptation, not a new bearer authentication flow.
The dependency never logs or returns token fields, and the caller key remains only in AuthContext
and the original allowed request header. The SDK mismatch response is deliberately **404**, matching
unknown sessions, instead of the initial plan's 403; this avoids confirming another session exists.
Every request still reauthenticates, so a rotated/locked/revoked key cannot reuse a live session.

FastAPI-MCP mounts GET/POST/DELETE with dependencies before delegating the same request scope to
the manager. Existing repository lifecycle startup remains intact. Add a startup guard that the
SDK exposes the reviewed AuthenticatedUser/AccessToken identity fields; update the lock requirement
only if installed source lacks the boundary. Locked 1.30.0 supports it; no dependency change needed.

## Caller discovery handler

Use the low-level server's public `request_handlers` mapping to replace only
`ListToolsRequest` with a handler returning `ServerResult(ListToolsResult(...))`. Extract the
authenticated original Request through `server.request_context.request`; request state carries
the private AuthContext set above. Missing context fails closed with a sanitized MCP error.
Use configured settings/upstream client from that Request's application and reuse the capability
service. The result is a fresh list of copied tool definitions, in the validated superset order.

Do **not** use the SDK `@server.list_tools()` decorator for caller-specific results: that
decorator mutates the shared `_tool_cache`, potentially removing schemas required by another
caller. Populate that cache once with the validated deployment superset; do not change it during
discovery. Guard the private cache shape at startup and keep this version-specific access inside
the MCP adapter. The original generated CallToolRequest handler/operation map/REST forwarding
remain intact, so guessed or cached hidden tools still pass request-specific REST authorization.
Startup validates the entire superset; it never requires a filtered list to equal that superset.

Pinned-key mode retains common discovery. Personal-key mode respects write admission and retains
conditional/unknown candidates, hiding only proven denials. No proactive list-change notification
is promised. A new tools/list and every call refresh auth/capability evidence. Upstream metadata
errors are sanitized rather than returning stale or another user's catalog.

## Review findings and resolution

| Finding | Severity | Resolution |
|---|---|---|
| CONTRACT-001: operation/context matrix incomplete | blocking | Resolved above for all eleven writes; exact field rules remain explicitly delegated |
| CONTRACT-002: tracker/non-member data could cause false grants/denials | blocking | Partial evidence states and inventory completeness rules resolved above |
| CONTRACT-003: dynamic list decorator mutates shared schema cache | blocking | Raw SDK handler plus immutable superset schema cache; named integration resolved |
| CONTRACT-004: session binding absent in current app | blocking | Adapt authenticated scope to SDK built-in owner boundary; 404 behavior documented |

Verdict: ready for the assigned implementation sequence. This source/document review completes
prep-010's evidence prerequisite; it does not establish runtime acceptance for prep-011 through
prep-014. The broader implementation request authorizes their coding and a distinct prep-014
verification stage. Unit tests and live writes are not run during the preceding coding stages.
