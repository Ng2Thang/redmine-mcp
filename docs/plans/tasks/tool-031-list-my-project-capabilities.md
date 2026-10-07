# tool-031: List my project capabilities

## 1. Task identity and status

| Field | Value |
|---|---|
| Task ID | tool-031 |
| Assigned capability | Inspect the caller's roles, permissions and candidate tools per visible project |
| Type | Add tool |
| Access | Read |
| Destructive effects | None |
| Status | blocked |
| Dependencies | Existing project reader and prep-010/011/012/013 implementations; runtime acceptance pending |
| Related tasks | tool-013; tool-028; prep-014 |
| Target Redmine version | Redmine 7.0.2; runtime acceptance pending |
| Last updated | 2026-10-05 |
| Progress summary | Permission aggregation and feature read rules implemented; follow-up checks and runtime acceptance pending |
| Next action | Obtain separate verification authorization before executing the scenarios in section 7 |

The user authorized `list_my_project_capabilities` implementation on 2026-10-05.
Implementation is finished; checks for the permission aggregation follow-up and runtime
acceptance are pending separate authorization.
The tool is read-only and targets Redmine 7.0.2. No configuration or dependency change is needed.

## 2. Discovery and evidence

`get_current_user` returns visible memberships and roles, but does not explain permissions
or tools per project. The existing capability gateway and necessary-permission checks are
reused. Upstream limitations and version evidence are recorded in
[prep-010](../prep-010-contract-review.md). Role permissions omit tracker/workflow restrictions.
Pre-existing prep-014 documentation edits and the relation endpoint correction were preserved.

## 3. Requirements and decisions

The user selected multiple projects, omission of blocked tools, and inclusion of unknown
candidates with explicit states. Return unique roles, merged project permissions and candidate tools for
the authenticated caller. Global tools are separate. Account and credential arguments are excluded.

## 4. Public contract and technical specification

- MCP: `list_my_project_capabilities`; read-only and idempotent annotations.
- REST: `GET /api/v1/users/current/project-capabilities`.
- Inputs: `limit=25` (1–100), `offset=0` (nonnegative), `include_reasons=false` (boolean).
- Optional `project_id` (positive integer) and `operation_id` (project-scoped tool name)
  filters combine. Operation filtering returns only the selected tool, conditional matches
  by default, and unknown matches when `include_unknown=true` (default false).
- Filters precede pagination; `total` counts matches. Scoped requests omit global tools.
  Global/unknown operation filters are rejected. A project lookup uses the caller-key
  project reader directly; hidden/missing targets retain upstream errors.
- Response: `user_id`, `items`, `total`, `limit`, `offset`, `visibility`, `global_tools`.
- Project: `id`, `name`, `roles`, nullable `permissions`, `permissions_state`,
  `membership_state`, `tools`.
- Role: `id`, nullable `name`, `inherited`. Missing upstream names remain null.
- Roles are deduplicated and sorted by ID. Direct membership takes precedence over the
  inherited flag when the same role occurs more than once.
- Project permissions are the sorted unique union of all readable membership roles.
  A permission granted by any role is included; role IDs/names do not rank privileges.
- `permissions_state` is `known` when all membership roles are readable, `partial` when
  some are readable, and `unknown` when no role is readable or membership is missing.
  Partial results retain the known union; unknown permissions are null.
- Tool: `operation_id`, `state` (`conditional` or `unknown`). `reason` is omitted by
  default and included only when `include_reasons=true`, for both project and global tools.

Unknown membership means no explicit evidence for the project; public/non-member access can
still exist. An empty known permission list means the reported membership roles have no
permissions, including a membership with no roles. Deployment-disabled, account-restricted
and denied writes are omitted.
Project read rules are centralized in `features/users/capability_rules.py`. Issue reads and
versions use `view_issues`; categories use `view_issues` OR `manage_categories`; files use
`view_files`; issue time entries require `view_issues` AND `view_time_entries` because the
gateway reads the issue first. Attachment reads use alternative container view permissions,
while the actual container and visibility remain invocation checks. `get_project` uses evidence
from the visible-project page. Explicit admin evidence makes mapped project reads conditional.
Positive evidence remains conditional when the permission union is partial. Without positive
evidence, reads remain unknown; non-member access can exist. Global and unmapped reads remain
unknown. Module, resource, private-issue and role visibility checks still apply on invocation.
Positive write evidence is conditional.
Relation deletion is an exception to omission on local denial: `delete_issue_relation` remains
unknown because permission on the other endpoint's project can authorize it. The report has no
relation target; invocation still resolves and checks both endpoints.

## 5. Implementation

The users router calls `ProjectCapabilityService`, which uses the existing project reader
Protocol and caller-key capability gateway. Bootstrap supplies the deployment write ceiling
and account admission. Existing authentication enforces pinned-key admission. Shared
`project_operation` evaluation is used by discovery and the report, without changing discovery
aggregation. No FastAPI or HTTPX imports are added to services.

One project page and the current profile are read per request. Role reads are deduplicated only
within the request. Global upload can require memberships outside the current page. An aggregate
deadline covers the report. Role 403/404 yields unknown evidence; other failures use existing errors.
No write or tool invocation is dispatched to infer permissions.

## 6. Acceptance criteria

Bind data to the caller; paginate visible projects; preserve named and inherited roles;
distinguish missing evidence from empty permissions; omit prohibited writes; retain conditional
and unknown candidates. Evaluate A/B independently. Separate global upload from project grants.
Preserve existing authentication and tool contracts except for the new catalog operation.

## 7. Test plan and execution record

No tests or runtime verification were created or executed. Separately authorized verification
should cover A/B permissions, multiple/inherited roles, role 403/404, missing memberships,
public projects without membership, malformed responses, upstream errors and deadlines;
reader/personal/pinned deployments, admin evidence and write ceilings; default/invalid pagination,
empty/later pages and shared-role deduplication; changes between requests and secret exclusion;
MCP discovery/invocation/annotations and existing catalog fixture updates; global/project separation.
Include a visible A–B relation where the caller has `manage_issue_relations` only on A:
the report for B must retain `delete_issue_relation` as unknown, with the cross-project
reason included when `include_reasons=true`.
Deployment/account restrictions must still omit the tool, and invocation authorization is unchanged.

## 8. Implementation and review record

The user requested merged permissions on 2026-10-05. Permissions now appear at project
level, with unique role metadata and explicit partial evidence. Per-role permission fields
were removed from this tool's response. This follow-up was inspected in source only;
no tests, static checks, startup checks or live calls were run for the aggregation change.
Separately authorized verification should cover overlapping and disjoint role permissions,
duplicate direct/inherited role IDs, mixed readable/unreadable roles, all unreadable roles,
empty memberships and a permission contributed only by a later role. Tool candidates should
appear once and retain the strongest available evidence (`conditional` over `unknown`).

Static checks for the original implementation, before the aggregation follow-up, executed
on 2026-10-05 using the installed environment:

- `.venv/Scripts/ruff.exe check .`: passed.
- `.venv/Scripts/ruff.exe format --check .`: passed; 191 files formatted.
- `.venv/Scripts/python.exe -m mypy src`: passed; 107 source files.
- `git diff --check`: passed; Git emitted existing CRLF normalization warnings.

Final source diff inspection confirmed caller-key wiring, read policy/catalog registration,
request-local role caching, aggregate deadlines and preservation of existing discovery behavior.
Startup, Inspector, tests, builds and live calls were not run. Existing test fixtures that
assert the exact operation catalog need an update in a separately authorized testing assignment.

## 9. Completion and handoff

The read reporting follow-up covers every current project read operation using centralized
OR/AND permission rules and explicit constraints. Evidence was inspected in the local pinned
`.local/upgrades/source/redmine-7.0.2.tar.gz`: core permission registrations, versions and
category authorization, project visibility, and attachment container models. The time-entry
AND rule also follows the existing gateway's issue preflight. Source inspection is not runtime
verification. No additional upstream calls or invocation authorization changes are introduced.
No tests or checks were run for this follow-up.
Separate verification should cover every mapping in the tool reference, permissions from one
or several roles, category alternatives, time-entry prerequisites split across roles, each
attachment container type and a mismatched container, explicit admin evidence, public projects,
partial evidence with a positive grant, missing/empty permissions, permissions in another
project only, disabled modules, private/restricted resources and unknown future operations.

Implementation finished; testing pending. Runtime acceptance requires a separately authorized
assignment covering section 7. Static checks do not establish runtime acceptance.

The optional explanation follow-up defaults `include_reasons` to false. Field-specific
serialization excludes absent reasons without removing nullable role names or permission evidence.
Both REST and MCP use the same router contract. No tests or checks were run for this follow-up.
Separately authorized verification should cover omitted/false/true input, invalid boolean
input, project/global read and write entries, cross-project relation reasons, retained null
evidence, and MCP input/output schema and serialized response behavior.

The scoped lookup follow-up adds project and operation filters. Cross-project operation
filtering inventories up to 100 pages of 100 projects under the existing aggregate deadline,
rejecting inconsistent totals, duplicate IDs and incomplete pages. Exceeding the inventory
bound produces an explicit error requesting project_id. Direct project lookup avoids that
inventory. Only the selected operation is evaluated when supplied. No tests or checks were run.
Separate verification should cover direct targets outside the default page, hidden/missing
projects, unknown/global operation names, disabled/account-restricted writes, conditional and
unknown matching, combined filters, filtering before pagination and exact totals, empty/later
pages, admin and public/non-member evidence, inventory changes/bounds and deadlines,
optional reasons, retained unfiltered behavior and MCP schema/invocation.

## Prep-020 evidence reconciliation, 2026-10-07

Current `list_my_project_capabilities` functional evidence is mapped in the
[32-operation ledger](../current-catalog-acceptance.md): 1086 offline and 21 owned 7.0.2 live
cases pass, including Inspector and cleanup. This preserves the preceding historical record;
it does not blanket close this owner's wider matrix. See H4 and the operation row for
matching criteria and exact remaining fixtures/role variants before claiming broader acceptance.
