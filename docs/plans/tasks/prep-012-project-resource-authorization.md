# prep-012-project-resource-authorization: Resolve caller capabilities by target

## 1. Task identity and status

| Field | Value |
|---|---|
| Task ID | prep-012-project-resource-authorization |
| Assigned capability | Reject known forbidden calls in the correct project/resource context |
| Type / access / destructive effects | Shared authorization prerequisite / existing read-write tools / Existing write effects preserved |
| Status | planned |
| Dependencies | [prep-010](prep-010-permission-session-contract.md) resolved matrix; [prep-011](prep-011-multi-user-writer-auth.md) personal-key auth |
| Related tasks | [Roadmap](../multi-user-writer-authorization.md); [dashboard](../index.md); prep-013/014 |
| Target Redmine version | 7.0.2; runtime acceptance pending |
| Last updated | 2026-10-05, Codex |
| Progress summary | Exact necessary expressions, context resolvers and partial evidence rules resolved by prep-010 |
| Blocker / next action | Implement after prep-011; use the dated prep-010 contract as the authoritative matrix |

## 2. Discovery and evidence

Client example: a user may create issues in project A and only read project B. A permission in
A must not authorize B. Current `Principal` has only user ID; `require_write_access` checks the
deployment/user/operation gates without resolved issue or container context.

Checked 2026-10-05: auth/security/bootstrap, users membership mapper, existing write routers and
task contracts, and the verified Redmine 7.0.2 archive. See the [dated evidence and archive hash](../multi-user-writer-authorization.md#baseline-evidence-and-limitations).
[Users API](https://www.redmine.org/projects/redmine/wiki/Rest_Users) supports caller memberships;
[Roles API](https://www.redmine.org/projects/redmine/wiki/Rest_Roles) supports role permissions.
Exact target source proves tracker settings are not included in role JSON, memberships are
visibility-filtered, own admin flag is available, and public non-member overrides affect access.
Runtime findings are pending. Initial working tree was clean; previous evidence stays unchanged.

Decision: use permission names and IDs, not role names. Preserve tool-013's current-user response;
do not add permission fields to that public schema or create a tool per role endpoint.

## 3. Requirements

| ID | Required observable behavior |
|---|---|
| REQ-001 | Context and capability evidence belong to the authenticated user and target project |
| REQ-002 | Role retrieval distinguishes trustworthy absence from partial, failed, or unknown data |
| REQ-003 | Each existing write checks applicable context without denying legitimate alternative permission paths |
| REQ-004 | Tracker/workflow/field/resource conditions remain enforced by Redmine under the same caller key |
| REQ-005 | Read behavior, write receipt semantics, and architecture remain compatible |

Scope: typed internal capability models, readers, resolver, policy, and integration with existing
tools. Excluded: generic CRUD, new public tools, complete recreation of Redmine authorization,
admin credentials, PostgreSQL access, cross-request caches, or unrequested test execution.

## 4. Public contract and technical specification

### Internal contract

Existing MCP names, operation IDs, REST routes, inputs/defaults and response schemas remain stable.
Keep application write admission/operation checks at the REST dependency boundary, shared by MCP.
Add typed context checks after validated inputs and existing target reads through service ports.

Internal records must include caller user ID, own admin status when explicitly present, visible
project membership role IDs/inherited flags, role permission names/visibility settings, and an
evidence completeness/reason indicator. Never retain the echoed user API key or unrelated profile
fields in the capability record. Keep credential-bearing AuthContext separate and secret-safe.

| Input/source | Mapping | Validation and absence behavior |
|---|---|---|
| Caller key | Existing auth context; same key on capability reads | Never supplied as tool argument or replaced by another credential |
| `GET /users/current.json?include=memberships` | User ID/admin and project role IDs | Strict IDs/booleans; absent membership is unknown coverage, not global denial |
| `GET /roles/{role_id}.json` | Permission names and visibility attributes | Validate requested/returned role ID; deduplicate within request; malformed data is upstream failure |
| Existing tool inputs and target reads | Actual source/destination project, issue/journal/attachment/relation context | Validate resource association; caller-supplied project cannot override resource ownership |

Within one project, preserve each role's permissions and visibility together. Do not construct
a synthetic grant by taking a permission from one role and a visibility/ownership condition
from another unless target source explicitly authorizes that combination. Across projects,
evaluate required conditions separately. The resolver never treats the role list as permission
to discover hidden resources.

Evidence states:

- `denied`: complete evidence proves every valid necessary permission path for this target is
  absent, or the deployment admission/operation ceiling forbids the call. Reject before mutation.
- `conditional`: an applicable permission path exists; final tracker/workflow/field/ownership
  checks still occur at Redmine. This is not an unrestricted grant.
- `unknown`: available API data cannot establish the context, e.g. public non-member override,
  missing admin evidence, or partial membership coverage. Do not convert unknown to a local grant
  or denial. Preserve normal same-key upstream authorization after deployment checks.

An optional role read returning 403/404 is unknown metadata rather than invalid caller identity;
401 from any capability read invalidates authentication. Timeout, 429, transport failure, or
malformed response must surface existing sanitized upstream errors and stop before mutation,
without silently falling back to an earlier successful snapshot. A genuine resource read 403/404
retains the existing resource error contract. No automatic retries and no probe mutations.

### Existing operation/context inventory

The following is a planning inventory from current contracts, not final permission evidence.
prep-010 must add exact 7.0.2 source branches for every alternative before coding this task.

| Operation | Context resolver | Permission/condition inventory to finalize |
|---|---|---|
| `upload_attachment` | Authenticated global upload, no target project | Dedicated upstream upload rule; never require invented project input or membership grant |
| `add_project_file` | Selected project and optional version association | `manage_files`; token ownership/consumption remains upstream |
| `update_attachment` | Prove declared project/version/issue container and resolve actual project | Project/version file permission versus issue tracker/own-issue edit alternatives |
| `delete_attachment` | Same container proof, before delete | File management versus tracker-aware `edit_issues`/`edit_own_issues` and visibility |
| `create_issue` | Destination project; optional visible copy source and its project | Destination `add_issues`; source `copy_issues` for copy; field/attachment/watcher checks delegated |
| `update_issue` | Existing issue project; optional destination project | Separate field editing/move conditions from notes-only `add_issue_notes`; privacy/own-issue/field rules |
| `update_issue_note` | Visible issue and journal belonging to it; journal author | `edit_issue_notes` or applicable own-note path; private note visibility remains upstream |
| `create_issue_relation` | Source issue project and visible target issue | Source relation permission and any target/cross-project requirements from exact source |
| `delete_issue_relation` | Resolve relation and associated issues | Exact source-versus-either-endpoint permission expression; do not assume one project |
| `add_issue_watcher` | Actual issue project | Add-watcher permission; target user eligibility and actual membership checked upstream/read-back |
| `remove_issue_watcher` | Actual issue project | Delete-watcher permission; direct/group watcher distinction retained |

Read tools keep current upstream visibility enforcement. Discovery has no target payload and
cannot make the same decision as invocation; prep-013 consumes capability evidence accordingly.

### Errors, success, and mutation semantics

Local known denial: existing sanitized 403 permission error, represented as a tool execution
error through the adapter. Existing 401/404/422/429/502/503/504 mappings remain applicable.
Success, no-body responses, pagination, receipts, and MCP result shapes remain existing tool
contracts. Writes retain no automatic retry, uncertain outcome reconciliation, independent
read-back, and task-owned cleanup; role checks do not provide locking or rollback.

Specification exit: resolved by the [prep-010 contract review](../prep-010-contract-review.md).
That source-backed matrix supersedes the initial inventory above, including the route OR expression
for mixed/notes-only issue updates and either-endpoint relation deletion. Discovery uses bounded
visible-project inventory to establish completeness. Partial permissions are not full authorization.

## 5. Implementation plan

| Step | Concrete ownership | Verification handoff |
|---|---|---|
| 1 | Resolve matrix/source branches and update this contract through prep-010 | PERM-001/002 |
| 2 | `auth/models.py`, `auth/ports.py`, policy/capability service: typed evidence and scoped evaluation | PERM-003/004 |
| 3 | `integrations/redmine/identity.py` and new role gateway; `bootstrap.py` wiring | PERM-005/006 |
| 4 | Existing feature services/ports/gateways: reuse context reads and apply typed authorization | PERM-007/008 |
| 5 | Security constants/error boundaries; document candidate/unknown semantics | PERM-009 |
| 6 | Coding static checks; hand off fixtures and execution to prep-014 | No tests during coding-only assignment |

No new runtime dependencies or public permission endpoint planned. Services must not import
FastAPI/HTTPX; MCP continues to reuse REST. Do not duplicate existing business validation.

## 6. Acceptance criteria and traceability

| Criterion | Requirement | Observable result | Scenarios |
|---|---|---|---|
| AC-001 | REQ-001 | Project A's grant cannot authorize project B or a forged resource project | PERM-003/007 |
| AC-002 | REQ-002 | Missing metadata, errors, inherited roles and admin evidence classified truthfully | PERM-004/005/006 |
| AC-003 | REQ-003 | All eleven writes use reviewed expressions; notes-only/own-resource alternatives work | PERM-001/002/008 |
| AC-004 | REQ-004 | Conditional/unknown calls use caller key and Redmine can still deny them | PERM-007/008 |
| AC-005 | REQ-005 | Existing reader contracts and accepted/uncertain receipts preserved | PERM-009 |

Results and execution evidence are pending for every criterion.

## 7. Test plan and execution record

Tests/fixtures/execution require a separate assignment. Reuse offline fake settings, MockTransport,
ASGI lifespan and MCP SDK clients. Synthetic permission/state checks are opt-in only.

| Scenario | Expected observable behavior | Mode |
|---|---|---|
| PERM-001 | Eleven source-backed expressions cover alternate paths and target resolution | Source/document review |
| PERM-002 | Upload, cross-project copy/move/relation and notes-only branches have exact contracts | Source/document review |
| PERM-003 | Different rights in A/B; no cross-project or cross-user grant leakage | Offline REST/MCP |
| PERM-004 | Multiple/inherited roles; no cross-role combination of unrelated constraints | Offline |
| PERM-005 | Admin flag, zero memberships, public non-member and group overrides are not false denials | Offline; synthetic |
| PERM-006 | Role ID mismatch, malformed permissions, 401/403/404/429/timeouts mapped without mutation | Offline |
| PERM-007 | Forged container/project, private resource, tracker restrictions, permission revoked after precheck | Offline; synthetic |
| PERM-008 | Own/other notes/issues, copy/move, relations, watcher eligibility; upstream decides final state | Offline; synthetic |
| PERM-009 | Read schemas, field mapping, no retries, accepted/uncertain and failed read-back remain compatible | Offline; synthetic |

| Evidence | Procedure | Actual / status |
|---|---|---|
| EVID-001 | Reviewed permission matrix and `bash scripts/check.sh` during coding | Not performed / pending |
| EVID-002 | Authorized selected PERM scenarios against credential-free baseline | Not run / pending |
| EVID-003 | Authorized marked synthetic permission and resulting-state checks | Not run / pending |

## 8. Implementation and review record

Planning only. No runtime or tests changed. Source gaps, downstream dependencies, and acceptance
remain pending. Existing task evidence is not rewritten as successful multi-user verification.

## 9. Completion and handoff

- [ ] Exact permission/context matrix resolved and reviewed.
- [ ] Typed capability evidence, adapters, and context checks implemented.
- [ ] Static checks and separately authorized acceptance evidence pass.
- [ ] Documentation, final diff, task status, and dashboard synchronized.

Final status: planned. Next action: implement the resolved prep-010 contract after prep-011.
