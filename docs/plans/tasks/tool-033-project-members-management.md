# tool-033: Project membership management

> Writer admission update (2026-10-13): pinned-key and user ID admission checks
> are retired. Earlier requirements and evidence below describe historical behavior.
> See [current configuration](../../configuration.md#separate-writer-deployment).

## 1. Task identity and status

| Field | Value |
|---|---|
| Task ID | tool-033-project-members-management |
| Assigned capability | Let an authenticated client list memberships and manage user memberships in explicitly selected projects. |
| Type | Four new MCP tools with a shared foundation owned by this single task. |
| Access | List is read-only; add, update, and delete require the separate enabled writer deployment. |
| Destructive effects | Removal or replacement of editable roles changes access; deletion removes membership and can affect inherited memberships and assignment defaults. |
| Status | complete |
| Dependencies | Existing project reader; prep-007 and prep-010 through prep-013 writer/auth/discovery implementations; prep-015 read budgets. Existing acceptance limitations remain in those records. |
| Related tasks | [tool-013](tool-013-get-current-user.md), [tool-031](tool-031-list-my-project-capabilities.md), [prep-016](prep-016-unit-testing.md), [prep-017](prep-017-offline-integration-testing.md), [prep-018](prep-018-live-e2e-testing.md). |
| Target Redmine version | Owned pinned Redmine 7.0.2; TOOL-033-011 passes in prep-020. |
| Last updated | 2026-10-07, Codex |
| Progress summary | All four tools have passing offline and owned native role/visibility/inheritance/assignment evidence; Inspector and disposable cleanup pass. |
| Next action | Use prep-020's current ledger; release and broader historical matrices retain their own owners. |

The user explicitly selected one task document for four separate tools. This overrides the
usual one-public-tool-per-task decomposition. Shared prerequisites stay here; no prep-019 or
tool-034 through tool-036 documents are assigned for these outcomes.

| Operation | Implementation status | Acceptance status |
|---|---|---|
| Shared models, preflight, receipts, and permission integration | Finished | Offline and owned 7.0.2 acceptance passed |
| `list_project_members` | Finished | Offline and owned 7.0.2 acceptance passed |
| `add_project_members` | Finished | Offline and owned 7.0.2 acceptance passed |
| `update_project_members` | Finished | Offline and owned 7.0.2 acceptance passed |
| `delete_project_members` | Finished | Offline and owned 7.0.2 acceptance passed |

## 2. Discovery and evidence

### Client outcome and repository baseline

The client needs to answer "Who belongs to projects A and B?" and manage individual users'
project roles without manipulating global accounts or groups. `get_current_user` reads only
the caller's memberships; `list_my_project_capabilities` reports caller roles and candidate
tools. Neither provides the project membership inventory or membership writes.

Applicable instructions are repository AGENTS.md, the user's documentation-only assignment,
[workflow](../../workflows/redmine-tools.md), and
[task template](../../templates/redmine-tool-task.md). All Markdown is English and suggested
commands are Git Bash. Do not implement code, write tests, run tests, or mutate Redmine in this
planning assignment. Preserve unrelated working-tree edits and historical acceptance evidence.

Reuse the following architecture and infrastructure:

- `features/projects/` for project contracts, routers, services, and Protocol ports; add a
  dedicated membership service rather than putting batch orchestration in routers.
- `integrations/redmine/` for async reads and single-attempt writes; `bootstrap.py` wires ports.
- `auth/policy.py`, capability models/resolver, and users capability rules/service for operation
  authorization and discovery; `mcp/catalog.py` owns explicit registration.
- Existing shared page, visibility, safe-error, read-budget, and write-receipt conventions.

The working tree was clean before this documentation assignment, apart from Git reporting
that `.pytest_cache/` could not be enumerated. No credentials or environment contents were read.

### Upstream evidence

The following public source files were read during planning on 2026-10-06. These are static
source findings, not runtime or acceptance results.

| Source | Version | Finding | Permission or limitation |
|---|---|---|---|
| [Memberships API](https://www.redmine.org/projects/redmine/wiki/Rest_Memberships) | General reference | Project membership list/create; individual membership read/update/delete; users and groups; inherited roles. | Wiki success-status examples do not override target source or runtime evidence. |
| [Members controller](https://svn.redmine.org/redmine/tags/7.0.2/app/controllers/members_controller.rb) | 7.0.2 | API authentication for index/show/create/update/destroy; index orders by membership ID; create returns the first created membership. | Use one native create per batch item; update/delete use the target's API success helper. |
| [Permission declarations](https://svn.redmine.org/redmine/tags/7.0.2/lib/redmine/preparation.rb) | 7.0.2 | `view_members` is public and maps to index/show; `manage_members` maps to membership writes and also index/show. | Read access is still constrained by Redmine project visibility/state. |
| [Member model](https://svn.redmine.org/redmine/tags/7.0.2/app/models/member.rb) | 7.0.2 | Project/principal pair is unique; inherited roles survive replacement; unmanageable roles are preserved; deletion requires no inherited roles and all roles manageable. | `manage_members` alone does not prove every role is editable; native propagation and callbacks remain authoritative. |
| [Users controller](https://svn.redmine.org/redmine/tags/7.0.2/app/controllers/users_controller.rb) | 7.0.2 | Individual user show is visibility-gated; global user index requires admin. | Add preflight may fail when the caller cannot prove the target is a visible user. No admin-key fallback. |
| [Role API serializer](https://svn.redmine.org/redmine/tags/7.0.2/app/views/roles/show.api.rsb) | 7.0.2 | Exposes role permissions and visibility settings. | Does not expose the full managed-role configuration; permission preflight has documented unknowns. |

Repository Compose pins 7.0.2, but the existing `redmine-mcp-test-redmine-1` container was
observed as `redmine:6.0.5-bookworm`, and its version source confirmed 6.0.5. This observation
does not establish 7.0.2 runtime behavior. Do not redeploy or replace data as part of planning.
Future live acceptance must first use an explicitly authorized, owned 7.0.2 synthetic environment.

| Outcome | Existing coverage | Access | Owner | Internal dependency |
|---|---|---|---|---|
| Project membership inventory | None; caller memberships only | Read | tool-033 | Shared models and gateway |
| Add a user's project membership | None | Write | tool-033 | Shared preflight and inventory mapping |
| Set a user's membership roles | None | Write | tool-033 | Shared preflight and membership lookup |
| Remove a user's project membership | None | Write | tool-033 | Shared preflight and membership lookup |

### Questions and decisions

| ID | Decision | Blocking? | Resolution date |
|---|---|---|---|
| DEC-001 | One task document owns four distinct public tools and their shared prerequisite work. | No | 2026-10-06 |
| DEC-002 | List users and groups; writes support users only. | No | 2026-10-06 |
| DEC-003 | Update sets requested roles; inherited/protected roles remain subject to native Redmine behavior. | No | 2026-10-06 |
| DEC-004 | Preflight the entire write batch before dispatch; return per-item results. | No | 2026-10-06 |
| DEC-005 | No automatic retries, rollback, implicit project descendants, global user search, or group mutation. | No | 2026-10-06 |
| DEC-006 | Full managed-role authority cannot be proved from the role API; report unknown evidence and verify actual observed roles. | No; explicit limitation | 2026-10-06 |

## 3. Requirements

### Goal and boundaries

Serve authenticated readers and project member managers. List is useful independently of the
writer. Add/update/delete affect only explicit user memberships. Preserve existing tool names,
contracts, caller authentication, deployment gates, and permission evidence semantics.

Out of scope: global account CRUD, group membership CRUD, user/role name search, automatic
membership migration between projects, changes to role definitions, and removal of inheritance
sources. Callers supply numeric IDs from Redmine or known references. Native effects on child
projects are consequences, not additional batch targets.

| ID | User need | Required observable behavior | Constraint |
|---|---|---|---|
| REQ-001 | Inspect selected projects | List a page per project with principal type, membership ID, roles, and inheritance. | One to ten explicit projects; independent page/error results. |
| REQ-002 | Add users | Create each requested project/user pair with requested roles; report existing membership explicitly. | User-only; do not convert add into update. |
| REQ-003 | Change roles | Send the requested role list and report requested versus observed roles and preserved inherited roles. | Do not change principal/project or promise all roles are editable. |
| REQ-004 | Remove users | Delete an eligible membership after confirming its project and user principal. | Block group and inherited memberships; native eligibility is final. |
| REQ-005 | Avoid preventable partial writes | Finish all preflight reads/checks before the first mutation. | Any determined preflight error prevents all writes. |
| REQ-006 | Understand batch results | Return ordered individual outcomes, verification, and safe errors. | No rollback/retry; distinguish uncertainty and unexecuted work. |
| REQ-007 | Enforce caller permissions | Apply reader/writer gates, operation allowlists, project evidence, and upstream authorization. | No admin fallback; unknown evidence is neither a grant nor a proven denial. |
| REQ-008 | Bound work and preserve compatibility | Reuse logical read budgets, page policy, lifecycle clients, and explicit MCP registration. | No unlimited scanning or cross-project authorization shortcut. |
| REQ-009 | Receive accurate documentation | Document contracts, role restrictions, destructive effects, and pending acceptance. | English Markdown; 6.0.5 container is not 7.0.2 acceptance evidence. |

Synthetic example: add user 27 with role 2 to projects 5 and 9. If project 9 is inaccessible
during preflight, project 5 must remain unchanged. If project 9 loses permission after a
successful preflight and project 5 has already accepted the write, report those results
individually; do not roll project 5 back.

## 4. Public contract and technical specification

### Tool and REST interface

Each operation has a stable ID matching its MCP name and a separate REST route.

| Operation | REST route | Exact caller-facing purpose | MCP annotations |
|---|---|---|---|
| `list_project_members` | `GET /api/v1/projects/memberships` | List one page of visible memberships for each selected project, including users, groups, roles, and inheritance. Each project has independent pagination and errors. | Read-only true; destructive false; open-world true. |
| `add_project_members` | `POST /api/v1/projects/memberships/batch` | Add user memberships to selected projects after whole-batch preflight. Report existing memberships and per-item acceptance separately from observed roles. Never automatically retry uncertain writes. | Read-only false; destructive false; idempotent false; open-world true. |
| `update_project_members` | `PUT /api/v1/projects/memberships/batch` | Set requested roles on selected user memberships after whole-batch preflight. Redmine preserves inherited or protected roles. Report per-item acceptance separately from actual roles. | Read-only false; destructive true; idempotent false; open-world true. |
| `delete_project_members` | `DELETE /api/v1/projects/memberships/batch` | Remove eligible user memberships after whole-batch preflight. Inherited memberships are retained. Report per-item acceptance separately from visible absence. | Read-only false; destructive true; idempotent false; open-world true. |

List uses the reader route dependency, `READ_OPERATIONS`, and base MCP catalog. Write routes
use `require_write_access`, `WRITE_OPERATIONS`, and the configured writer catalog. Register
routes before MCP creation. Preserve required body arrays in the generated MCP schemas.

### Inputs

Use typed requests, forbid unknown body fields, reject booleans as IDs, and preserve input
order. Invalid request shape is a global validation error before upstream work.

| Field | Type and rule | Required/default | Mapping and null/empty behavior |
|---|---|---|---|
| List `project_ids` | Unique positive integer array, 1-10 entries; repeated REST query parameter | Required | One upstream project path per entry; null/empty rejected. |
| List `limit` | Integer, 1-100 | 25 | Per-project upstream page size. |
| List `offset` | Nonnegative integer | 0 | Same offset applied independently to each requested project. |
| Write `items` | Typed array, 1-10 entries | Required | Body array; null/empty rejected. |
| All write items `project_id` | Positive integer | Required | Create destination or declared existing membership project. |
| Add item `user_id` | Positive integer | Required | Native `membership.user_id`; must first be proved to identify a visible user. |
| Update/delete item `membership_id` | Positive integer | Required | Native membership path; actual project must match `project_id`. |
| Add/update item `role_ids` | Unique positive integer array, at least one entry | Required | Native `membership.role_ids`; null/empty rejected. |

Reject repeated add `(project_id, user_id)` targets and repeated update/delete membership IDs
in the same request. One project or one item is supported by an array of length one. Changing
principal or project is not an update field. Role IDs are references, not permission names.

### Outputs and mapping

Define `ProjectMembership` with `id`, `project:{id,name}`, exactly one of
`user:{id,name}` or `group:{id,name}`, `roles:[{id,name,inherited}]`, and `visibility`.
Default an omitted inherited flag to false only as allowed by the native serializer contract.
Normalize repeated native role IDs in first-seen order, using `inherited=true` if any source
is inherited. This includes mixed direct/inherited rows; deletion must retain inheritance
restrictions. Reject conflicting names for the same role ID and malformed role fields.
Do not apply this normalization to requested write role IDs: duplicate inputs remain invalid.
Missing/malformed principal, project, IDs, collections, or role flag types are upstream errors;
never silently map missing collections to empty lists. Return only allowlisted public fields.

List returns `results` in project input order. Each result contains `project_id`, `outcome`
(`read`, `rejected`, or `not_executed`), nullable `page`, and nullable safe `error`.
A successful page uses existing `Page[ProjectMembership]` metadata: items, total, limit,
offset, visibility, and pagination_policy. Never flatten project totals into a member count.
Continue a selected project by calling again with that project and its next offset. Respect
`requires_narrowing`, scope errors, changing totals, and logical read budgets.
Project-specific `scope_required` errors do not stop reading the other selected projects.
Shared credential, transport and logical read-budget failures can stop later project reads.

Writes return `phase` (`preflight_failed` or `executed`) and ordered `results`. Each item has:

- `index`, `project_id`, nullable `membership_id`, and nullable `user_id`.
- `outcome`: `accepted`, `rejected`, `uncertain`, or `not_executed`.
- `verification`: `matched`, `mismatch`, or `unavailable`.
- Nullable `requested_role_ids`, `observed_membership`, and `observed_present`.
- `permission_state`: `conditional`, `unknown`, or `denied`, reflecting necessary evidence.
- Nullable safe `error:{code,message,status}`; no raw upstream error body or credentials.

For preflight rejection, the failing items are `rejected`; eligible peers are `not_executed`
with a batch-preflight reason. Verification is `unavailable` when no read-back applies.
Return an existing readable membership for a rejected duplicate add. Add/update read-back
compares effective observed role IDs with requested role IDs, reporting `mismatch` when native
protection or filtering changes the result. Inherited flags explain retained roles; do not
claim the API proves all preserved roles' management restrictions.

| Operation | Minimum upstream calls and mapping | Native acceptance |
|---|---|---|
| List | `GET projects/{id}/memberships.json?limit=...&offset=...`, ordered natively by membership ID | 200 with memberships and page metadata. |
| Add | Prove project/user and inspect visible target-user memberships; `POST projects/{id}/memberships.json` with `{"membership":{"user_id":27,"role_ids":[2]}}`; read returned membership ID | 201 with one membership; read-back separately verifies fields. |
| Update | `GET memberships/{id}.json`; `PUT memberships/{id}.json` with `{"membership":{"role_ids":[2,3]}}`; read the same ID again | Accept native 200 or 204 success; an empty success body is valid. |
| Delete | `GET memberships/{id}.json`; `DELETE memberships/{id}.json`; reconcile visible absence | Accept native 200 or 204 success; an empty success body is valid. |

Use `GET users/{id}.json?include=memberships` for add user proof and a visible duplicate
lookup. If this lookup is incomplete, inspect the target project's membership pages only
within the permitted page/read budgets; inability to complete duplicate proof fails preflight.
`GET roles.json` supplies the givable role catalog for ID validation, not the caller's managed
role set. Individual role reads supply necessary caller permission evidence when available.
Deduplicate these reads within a request without persisting authorization across requests.

Batch envelopes use HTTP 200, including per-item resource/preflight errors; MCP returns that
structured envelope. Request-level validation/authentication/gate failures retain normal HTTP
errors and the existing MCP error mapping. Additive tools do not alter existing contracts.

Synthetic inputs:

```json
{"project_ids":[5,9],"limit":25,"offset":0}
```

```json
{"items":[{"project_id":5,"user_id":27,"role_ids":[2]},{"project_id":9,"user_id":27,"role_ids":[2]}]}
```

```json
{"items":[{"project_id":5,"membership_id":101,"role_ids":[2,3]}]}
```

```json
{"items":[{"project_id":5,"membership_id":101}]}
```

Synthetic partial execution receipt:

```json
{
  "phase":"executed",
  "results":[
    {"index":0,"project_id":5,"membership_id":101,"user_id":27,
     "outcome":"accepted","verification":"matched","requested_role_ids":[2],
     "observed_membership":{"id":101,"project":{"id":5,"name":"Project A"},
       "user":{"id":27,"name":"Demo User"},"group":null,
       "roles":[{"id":2,"name":"Developer","inherited":false}],
       "visibility":{"scope":"requesting_redmine_user","observations":[]}},
     "observed_present":true,"permission_state":"conditional","error":null},
    {"index":1,"project_id":9,"membership_id":null,"user_id":27,
     "outcome":"uncertain","verification":"unavailable","requested_role_ids":[2],
     "observed_membership":null,"observed_present":null,"permission_state":"conditional",
     "error":{"code":"write_outcome_uncertain","message":"Reconcile before retrying.","status":null}}
  ]
}
```

### Authentication and authorization

Use the caller's authenticated API key or the configured restricted writer identity. Never
fall back to an administrator key. Keep writer enablement false by default, require an
explicit operation allowlist, and honor pinned-key/personal-key user restrictions.

List does not require `manage_members`. In 7.0.2 `view_members` is public, so missing role
permission entries cannot establish a read denial. Add a project read capability rule with
public-read semantics, constrained by actual project access on invocation. Do not claim
compatibility with the running 6.0.5 permission behavior.

For each write, resolve the actual destination project and evaluate `manage_members` through
the existing capability service. Merge readable role permissions; never infer authority from
role names. Add/update/delete require this permission on each explicit target project.
Admin overrides Redmine role evidence, but not MCP writer gates or operation configuration.

For update/delete, validate actual membership project and user principal before authorization
and dispatch. A group target fails preflight. A project mismatch fails with a safe validation
error. Memberships with any inherited role fail delete preflight, including inheritance from
groups or parent projects. Do not remove inheritance sources automatically.

Necessary permission states remain `conditional`, `unknown`, and `denied`. Determined denial
fails preflight; unavailable permission metadata is reported as unknown and left to upstream
authorization after required target proofs have completed. Missing target proof is a separate
preflight failure. Role catalog validity does not establish permission to assign that role.
Redmine can silently preserve/filter roles, so even a 204 response is not proof of an exact
requested role change.

Expose these rules through `list_my_project_capabilities` and MCP discovery. Refresh caller
permission evidence after accepted writes affecting the caller; do not reuse a preflight
snapshot as a durable grant. Recheck necessary target evidence before subsequent dispatches
subject to the same logical budget. Upstream remains the final authorization authority.

### Errors

| Scenario | Detection/result | Retry or reconciliation |
|---|---|---|
| Invalid array size, IDs, duplicates, fields, or missing roles | Request validation, HTTP 422 before upstream access | Correct request. |
| Missing/invalid authentication | Existing auth error, HTTP 401 | Supply valid caller credentials. |
| Writer disabled, caller restricted, or operation absent from allowlist | Global HTTP 403 before any batch mutation | Correct authorized deployment configuration. |
| Preflight forbidden/missing project, membership, or user | Item `rejected`, safe 403/404; peers not executed | No write dispatched. |
| Group write target, project mismatch, inherited delete, invalid roles, existing add | Item `rejected`, safe 422; peers not executed | Use explicit supported targets/action. |
| Malformed preflight response | Item `rejected`, safe upstream-response 502 | No write dispatched; fix upstream contract. |
| Preflight page/read budget exhausted | Item rejection with existing scope/budget code; remaining work not executed | Narrow batch or scope; no unlimited scan. |
| Native 400/422 mutation rejection | Item `rejected`, sanitized 422 | Reconcile current state before a changed request. |
| Permission/resource error after preflight | Item `rejected`, safe 403/404 | Continue independent items; earlier accepted items remain accepted. |
| Native credential failure during execution | Reject failing item; stop and mark remaining items not executed | Reauthenticate and reconcile previous writes. |
| Timeout or unexpected response after dispatch | Item `uncertain` | Reconcile by membership ID or project/user pair; never auto-retry. |
| Shared transport outage, budget exhaustion, or interruption | Stop new dispatches; preserve prior receipts, classify in-flight write uncertain when delivery cannot be proved, mark remaining items not executed | Reconcile attempted items before resuming. |
| Read-back fails or returns conflicting fields | Preserve acceptance/uncertainty; verification unavailable/mismatch | Do not equate failed verification with failed mutation. |

If client disconnection prevents delivering the receipt, no further writes are scheduled.
The caller must reconcile every attempted or potentially attempted target before resubmission;
no durable operation log or exactly-once guarantee is introduced by this task.

### Write semantics and execution policy

1. Validate request shape before upstream work. Preflight all items without mutation: prove
   targets, project identity, user type, role IDs, duplicate absence for add, inheritance for
   delete, and necessary permission evidence. Return all determined failures when budget allows.
2. If any check fails or cannot complete, dispatch nothing. Return preflight errors and explicit
   not-executed peers; unknown managed-role authority alone is not a fabricated denial.
3. Once preflight succeeds, dispatch one native write at a time in input order. Native per-item
   rejection does not undo accepted peers. Stop on shared credential, transport, budget, or
   cancellation conditions. Do not retry or reorder writes.
4. Perform bounded read-back for attempted writes. For delete, a readable project and absent
   membership in a complete permitted inventory can prove visible absence. A bare 404 or lost
   project access is insufficient; return unavailable if absence cannot be established.

This is not a Redmine transaction: permissions and state can change between checks and writes.
Concurrent updates have no application-level compare-and-swap guarantee. For add, a concurrent
create may cause a native duplicate rejection; read the existing membership when feasible.
Repeated add does not update roles; repeated delete may encounter an absent target. No call
automatically retries any mutation or rolls back previous results.

Adding/changing roles can propagate native membership effects to descendants configured for
inheritance. Deleting a membership can remove default assignee references on its project and
issue categories, in addition to native propagation. Read-back verifies only the explicit
membership outcome, not every descendant or assignment side effect. Plan live checks for
these effects and document that restoring membership does not necessarily restore defaults.

Reuse single-attempt writer transport, shared response limits, and logical read budgets.
Membership enumeration cannot bypass the existing maximum-query-pages policy. Reuse safe
logging without principal payloads, keys, tokens, or complete upstream error bodies.

For future verification use only owned synthetic users/projects/roles. Snapshot the relevant
membership and default assignment state before authorized mutations; cleanup restores only
owned resources. Group inheritance fixtures may be prepared administratively outside these
tools. Never reset/restore an unmarked environment.

Specification exit check: public behaviors are specified; native managed-role restrictions
and runtime version mismatch are explicit limitations, not unresolved implementation choices.

## 5. Implementation plan

| Step | Change | Components | Depends on | Planned review/verification |
|---|---|---|---|---|
| 1 | Shared typed membership/page/batch models, Protocols, ordered receipts and preflight rules | Project membership feature and Redmine gateways | Existing reader/writer/read-budget baseline | Contract and architecture review; scenarios 001, 003, 005 |
| 2 | Shared target resolution, permission expressions, writer operation gates and request-local evidence refresh | Auth capability models/resolver, policy, bootstrap | Step 1 | Permission/discovery scenarios 004, 010 |
| 3 | List route/service/gateway; public-read discovery rule and independent project pages | Project membership reader and users capability rules | Step 1 | Scenarios 001, 002, 004 |
| 4 | Add user proof, duplicate preflight, single-item native create and read-back | Membership writer/service | Steps 1-3 | Scenarios 005, 006 |
| 5 | Update declared-project proof, requested-role mapping and observed-role comparison | Membership writer/service | Steps 1-4 | Scenario 007 |
| 6 | Delete inheritance checks, native eligibility handling and absence verification | Membership writer/service | Steps 1-5 | Scenario 008 |
| 7 | Register four operations and preserve REST-backed schemas/annotations | MCP catalog, registration, discovery, bootstrap | Steps 3-6 | Scenario 010 |
| 8 | Update tool reference, configuration, manual verification and roadmap status | Existing documentation | Steps 1-7 | Documentation and contract review |
| 9 | Separately authorized test implementation/execution and synthetic acceptance | Existing offline/live test layers | Steps 1-8 and explicit testing assignment | Scenarios 001-011; record actual evidence |

Sequence is shared foundation -> list -> add -> update -> delete -> documentation. Permission
integration is shared and must exist before exposing writes. No dependency on implementing a
new global users tool is introduced. No new package dependency or lockfile change is planned.

Required future documentation changes:

- `docs/tool-reference.md`: all four names, request/response examples, page and batch behavior,
  native role restrictions, uncertain writes, and scoped capability discovery.
- `docs/configuration.md`: explicit writer operation names and unchanged pinned/personal-key
  gates; no automatic enablement or widening to all users.
- `docs/manual-verification.md`: synthetic reader/writer permissions, state/side-effect checks,
  reconciliation, task-owned cleanup, and exact-version prerequisite.
- This task and `docs/plans/index.md`: per-operation progress and overall status in the same change.

## 6. Acceptance criteria and traceability

| ID | Given/when | Required result |
|---|---|---|
| AC-001 | List one or several visible projects | Ordered independent pages expose correct principal/role/inheritance data and pagination. |
| AC-002 | Valid add or an existing project/user membership | Create exactly one native membership per item, or return explicit existing-membership rejection without updating it. |
| AC-003 | Update with editable, protected, and inherited roles | Apply native semantics and report exact requested/observed sets without inventing a grant. |
| AC-004 | Delete user, group, inherited, and restricted-role targets | Only eligible user targets are dispatched; native restrictions and visible absence are correctly reported. |
| AC-005 | Any preflight failure or incomplete bounded preflight | No mutation is dispatched; every item has a rejection/not-executed result. |
| AC-006 | A post-preflight failure, uncertainty, or read-back error | Preserve prior receipts, stop shared failures, report per-item results, and never retry/rollback. |
| AC-007 | Reader/writer gates and differing project roles | Enforce operation/project boundaries and keep conditional/unknown evidence advisory. |
| AC-008 | Invalid input, malformed upstream data, or budget exhaustion | Safe bounded errors; no missing collection interpreted as empty or unbounded scan. |
| AC-009 | MCP discovery and existing tools | Register four exact names with correct schemas/annotations; existing contracts remain compatible. |
| AC-010 | Future live acceptance | Verify caller permissions, resulting membership state and native side effects on owned 7.0.2 data. |

| Requirement | Acceptance criteria | Scenarios | Evidence/result |
|---|---|---|---|
| REQ-001 | AC-001, AC-008 | TOOL-033-001, 002, 003 | EVID-033-OFFLINE: covered offline variants pass |
| REQ-002 | AC-002, AC-005 | TOOL-033-005, 006 | EVID-033-OFFLINE: covered offline variants pass; native state pending 011 |
| REQ-003 | AC-003 | TOOL-033-007 | EVID-033-OFFLINE: simulated role retention passes; native roles pending 011 |
| REQ-004 | AC-004 | TOOL-033-008 | EVID-033-OFFLINE: delete proofs pass; native restrictions/side effects pending 011 |
| REQ-005 | AC-005 | TOOL-033-004, 005 | EVID-033-OFFLINE: covered preflight variants pass |
| REQ-006 | AC-006 | TOOL-033-009 | EVID-033-OFFLINE: covered partial/uncertain/interrupted variants pass |
| REQ-007 | AC-007 | TOOL-033-004, 010, 011 | EVID-033-OFFLINE: mocked gates/evidence pass; native authorization pending 011 |
| REQ-008 | AC-008, AC-009 | TOOL-033-002, 003, 010 | EVID-033-OFFLINE: covered validation/budget/schema variants pass |
| REQ-009 | AC-009, AC-010 | TOOL-033-010, 011 and documentation review | EVID-033-OFFLINE and documentation updated; EVID-033-LIVE pending |

## 7. Test plan and execution record

### Scenario plan

The original planning assignment wrote no tests. The follow-up testing assignment explicitly
authorized offline test implementation and execution on 2026-10-06. The tests reuse
pytest/pytest-asyncio, HTTPX MockTransport, ASGI lifespan, and the MCP SDK. Live scenarios
remain explicitly opt-in and require the owned target-version environment.

| Scenario | Criteria | Layer/setup | Expected result | Mode |
|---|---|---|---|---|
| TOOL-033-001 | AC-001 | Reader gateway/REST: user, group, mixed/inherited roles, repeated role IDs from multiple sources and mixed direct/inherited rows, empty list, two projects | Exact mappings and stable input order; role IDs normalized with any-source inheritance; no invented principal or missing-array default. Exercise the same normalization in user duplicate proof and add/update read-back. | Offline |
| TOOL-033-002 | AC-001, AC-008 | Page metadata, successive offsets, differing totals, scope/page/read budgets; one project over page scope and another within scope | Independent policy metadata; project scope rejection does not skip a readable peer; shared budgets still stop later work; partial/error results do not imply complete inventories. | Offline |
| TOOL-033-003 | AC-008 | Invalid size/IDs/duplicates/body fields; malformed principal/roles/page data; conflicting names on repeated native role IDs | Request validation precedes upstream calls; malformed responses produce sanitized errors; repeated valid upstream rows are normalized while duplicate requested role IDs remain invalid. | Offline |
| TOOL-033-004 | AC-005, AC-007 | Manager in A but not B; admin; merged/inherited roles; missing metadata; public read | No write on known mixed-batch denial; unknown evidence is not a false grant/denial; list does not require manage_members. | Offline |
| TOOL-033-005 | AC-005 | One invalid, duplicate, inaccessible, group, or mismatched target; exhausted preflight budget | Entire batch mutation count zero; ordered rejected/not-executed results. | Offline |
| TOOL-033-006 | AC-002 | Add user proof, givable roles, native 201, existing/concurrent duplicate | One native create per item; no update fallback; existing membership returned when readable. | Offline |
| TOOL-033-007 | AC-003 | Native role filtering, protected/inherited retention, 200/204, changed observed roles | Acceptance and actual role match differ correctly; no claim all roles were editable. | Offline |
| TOOL-033-008 | AC-004 | Eligible delete, group/inherited target, unmanageable native rejection, missing/access-lost read-back | Correct dispatch boundaries and absence proof; access loss is not proof of deletion. | Offline |
| TOOL-033-009 | AC-006, AC-008 | Mid-batch 403/422, credential failure, timeout, cancellation, shared outage, failed read-back; deadline expires while a mutation waits for admission | Correct accepted/rejected/uncertain/not-executed classification; no expired queued dispatch, permit released and earlier receipts retained; direct/proxy transport and reader compatibility; one write attempt, no rollback. | Offline |
| TOOL-033-010 | AC-007, AC-009 | MCP schemas, list and each write invocation, annotations, gate/allowlist, scoped discovery and caller role revocation | Four exact tools; reader exposes list; writes follow configuration and fresh evidence; existing tools preserved. | Offline REST/MCP |
| TOOL-033-011 | AC-007, AC-010 | Owned 7.0.2 environment with contrasting ordinary users, parent/child inheritance, protected roles and default assignments | Inspector results match native access and actual state; effects and cleanup documented. | Explicitly authorized live |

Coverage of defaults/optional fields/pagination: 001-003. Authentication and permission
boundaries: 004, 010, 011. Exact payloads/no-body success/duplicates: 006-008. Uncertain outcomes
and interruption: 009. Startup, state and cleanup: 011. Name search/encoding is N/A because
this contract uses numeric IDs and does not expose a free-text search.

### Offline scenario ownership

The following files add 155 collected cases: 86 unit/service/gateway cases and 69 REST/MCP
integration cases. Native permission, inheritance and side-effect behavior is simulated here;
passing offline assertions does not establish Redmine 7.0.2 runtime acceptance.

| Scenarios | Implemented offline coverage |
|---|---|
| 001-003 | `tests/unit/test_project_members.py`: strict IDs, batch bounds, duplicates, roles and principals; `tests/integration/test_project_members.py`: reader REST/MCP pagination, groups, empty continuation, malformed pages; `tests/unit/test_project_members_gateway.py`: repeated-role normalization in read-back. |
| 004-005 | Unit permission evidence covers admin, unknown and merged/inherited roles; integration covers mixed project permissions, zero-mutation preflight, group/inherited targets, project mismatch, missing targets, unknown roles, existing users and exhausted request/byte budgets. |
| 006-008 | Integration checks all three native payloads and REST/MCP calls, concurrent duplicate observation, missing user expansion with complete multi-page inventory, changing/short inventories, protected role retention, empty 200/204 update responses and delete absence/access-loss/mismatch proofs. Gateway tests preserve acceptance for invalid create receipts. |
| 009 | Integration checks independent 403/422 versus shared 401/5xx/timeout execution failures, retained receipts after deadline/read-back failures and no retry/rollback. Unit tests cover external cancellation and expired queued GET/POST/PUT/DELETE dispatch with permit release; existing `test_bounded_reads.py` covers shared direct/proxy admission. |
| 010 | Integration checks reader/writer operation discovery, MCP schemas/annotations, DELETE body forwarding, capability reporting, operation allowlists, personal/pinned caller restrictions and refreshed permissions after an earlier item. Existing reader catalog checks include the new list operation and its per-project errors. |
| 011 | Pending: real 7.0.2 project visibility, managed roles, parent/child inheritance, default-assignee effects, Inspector and task-owned cleanup. |

Reproduce the authorized offline checks from Git Bash at the repository root:

```bash
uv --cache-dir .local/uv-cache run --frozen --no-sync pytest tests/unit tests/integration -q -p no:cacheprovider
uv --cache-dir .local/uv-cache run --frozen --no-sync ruff check .
uv --cache-dir .local/uv-cache run --frozen --no-sync ruff format --check .
uv --cache-dir .local/uv-cache run --frozen --no-sync mypy src
git diff --check
```

The workspace uv cache uses installed locked dependencies without synchronizing. Pytest's
optional cache provider is disabled because this sandbox denies cache-directory creation.
Offline isolation blocks external HTTP transports and removes Redmine environment variables.
No live server, credentials, Docker state, dependency lockfile or deployment configuration is
changed by these tests.

### Execution evidence

| Evidence ID | Procedure | Expected | Actual result | Status/date |
|---|---|---|---|---|
| EVID-033-PLAN | Read repository contracts and versioned public source; create combined plan and dashboard entry | Nine sections, one owner, explicit contracts and pending scenarios | Planning documentation only; no runtime assertion | Recorded 2026-10-06 |
| EVID-033-STATIC | Installed Ruff lint/format and mypy; final diff inspection (commands in section 8) | Runtime static checks pass after implementation | Ruff and mypy pass; final diff checked | Recorded 2026-10-06 |
| EVID-033-REVIEW-STATIC | Repeat installed Ruff lint/format, mypy and diff inspection after the three review fixes | Review fixes satisfy static checks | Ruff lint passes; 230 files formatted; mypy passes for 118 source files; diff check passes | Recorded 2026-10-06; runtime scenarios pending |
| EVID-033-OFFLINE | Authorized offline command above, with external transports blocked | Feature cases and existing compatibility pass | 736 passed, 1 existing Pydantic deprecation warning, 214.93 seconds; includes 155 new feature cases | Passed 2026-10-06 |
| EVID-033-TEST-STATIC | Installed Ruff lint/format, mypy and diff inspection after test additions | Static checks and whitespace pass | Ruff lint passes; 234 files formatted; mypy passes for 118 source files; diff check passes | Passed 2026-10-06 |
| EVID-033-LIVE | Future authorized `uv run --frozen pytest tests/e2e --run-e2e` and selected Inspector procedures | Owned 7.0.2 permission/state acceptance and cleanup | Not run; running container was observed as 6.0.5 | Pending |

Commands above are proposed future execution, not authorization to run them. Builds are
N/A unless implementation changes packaging/dependencies. Source inspection and earlier
unrelated acceptance records do not satisfy these scenarios.

## 8. Implementation and review record

- Review follow-up on 2026-10-06 addressed all three source-review findings. Native role rows
  now normalize by ID with any-source inheritance, across membership models and user duplicate
  lookup. First-seen order is preserved; inconsistent names and invalid flags remain errors.
  Write input duplicates remain rejected. This corrects handling of valid Redmine MemberRole
  rows without weakening inherited-delete restrictions.
- Project pagination scope errors now remain local to the list result. Shared budget/auth/
  transport failures still stop later work; write preflight failure rules are unchanged.
- The shared admitted transport now checks the active read deadline after acquiring capacity
  and before forwarding to its inner transport. Its existing exception cleanup releases the
  permit, with dispatch evidence still false. Membership batches retain accepted peers and
  reject an expired queued request without further mutation dispatch.
- Follow-up docs cover these semantics and expand scenarios 001, 002 and 009 above, including
  role normalization in add/update paths and queue/permit/direct/proxy reader compatibility.
  At that coding stage, test additions/execution remained pending separate authorization;
  no tests or live calls were
  performed for the follow-up. Follow-up static-check results are recorded below.

- Planning history: the combined task and roadmap entry were created before the separate
  tool-033 implementation assignment. Planning itself changed no runtime or live state.
- Plan deviation: four tools share one task at the user's explicit request; shared foundation
  remains internal. Public reader/write separation is preserved.
- Implementation finished on 2026-10-06: dedicated project membership models, Protocols,
  service, router and native Redmine gateway; whole-batch preflight and sequential writes;
  positive IDs, bounds, duplicates, user-only targets and actual-project validation.
- Reader mapping includes users/groups and inherited roles. Add proves a visible user, uses
  its membership expansion with bounded project inventory fallback, reports existing and
  concurrent duplicates explicitly, and never converts add to update.
- Native update preserves inherited/protected roles. Delete rejects inherited/group targets
  and verifies absence only using a complete bounded project inventory. Accepted writes retain
  their outcome when subsequent observation fails. Uncertain/shared failures stop later work.
- Permission integration includes the public 7.0.2 read rule, necessary `manage_members`
  evidence for all writers, fresh evidence between writes, explicit MCP catalogs/annotations,
  capability reporting/discovery and existing enabled-writer/allowlist/user gates.
- Compatibility detail discovered during coding: FastAPI-MCP 0.4 drops DELETE bodies. A
  narrowly scoped adapter forwards the membership DELETE JSON body. The three writer MCP
  schemas also retain the top-level unknown-field restriction.
- Membership writes share one bounded read context across preflight, rechecks and read-back.
  It checks deadline before dispatch without an outer cancellation timer that could erase an
  accepted receipt. External cancellation propagates; delivery after disconnect/shutdown is
  not guaranteed and requires caller reconciliation. Membership server errors after dispatch
  are uncertain; no automatic retries or rollback are introduced.
- Tool reference, writer configuration, manual verification guide and changelog updated.
  Deployed configuration, credentials, dependencies and lockfile are unchanged.
- Static commands use the existing environment and a workspace cache because access to the
  default user uv cache was denied. No dependency installation or tests were performed:

  ```bash
  uv --cache-dir .local/uv-cache run --frozen --no-sync ruff check .
  uv --cache-dir .local/uv-cache run --frozen --no-sync ruff format --check .
  uv --cache-dir .local/uv-cache run --frozen --no-sync mypy src
  git diff --check
  ```

  Ruff lint/format and mypy passed. Formatting/import fixes were limited to changed files.
  Unit/integration/E2E tests, test edits, startup, Inspector, builds and live verification were
  not performed. Git Bash process launch was unavailable in the sandbox; the prerequisite
  doctor script could not be executed. Installed static executables were used directly.
- Existing evidence limitations: upstream managed-role configuration is not fully exposed;
  configured 7.0.2 differs from the container observed during planning.
- Diff review: scoped runtime and documentation changes preserve prior evidence and existing
  tools; no tests, credentials, generated manifests or non-English Markdown are included.

- Follow-up testing assignment completed on 2026-10-06: 155 new offline cases, shared synthetic
  memberships/roles/user expansion, and existing reader catalog/error checks. The final full
  unit/integration run passed 736 cases. Ruff lint/format, mypy and diff checks passed.
  Initial failures were corrected test expectations and fixture handling; runtime code did not
  require changes. One existing dependency Pydantic deprecation warning remains. No live
  startup, Inspector, E2E execution, Docker mutations or real Redmine writes were performed.

## 9. Completion and handoff

- [x] One combined task owns the four agreed outcomes and shared prerequisites.
- [x] Public contracts, permission behavior and verification scenarios are documented.
- [x] Shared foundation and permission integration implemented.
- [x] List implemented and accepted.
- [x] Add implemented and accepted.
- [x] Update implemented and accepted.
- [x] Delete implemented and accepted.
- [x] Every requirement has passing acceptance evidence.
- [x] Required static checks and authorized offline tests pass.
- [x] Required 7.0.2 live state/permission/side-effect verification completed.
- [x] Tool reference, configuration and manual verification reflect implemented behavior.
- [x] Implementation diff reviewed and dashboard synchronized with actual progress.

Overall status: **blocked; implementation and offline testing finished; 7.0.2 live acceptance pending**.

Passing offline tests does not enable a deployed writer or establish native target-version
acceptance. Retain operation-level evidence and keep overall status `blocked` until scenario
011 supplies the required native state, permission and side-effect evidence.

### Current acceptance reconciliation, 2026-10-07

The preceding blocked result is the historical offline handoff. The user subsequently assigned
[prep-020](prep-020-current-catalog-acceptance.md), authorizing TOOL-033-011 against owned 7.0.2.
`tests/e2e/test_catalog_acceptance.py` now observes ordinary manager/readers, public/private
membership visibility, native managed-role filtering, protected-role retention and explicit
accepted/mismatch observation, protected deletion rejection, inherited/group deletion denial,
parent/child propagation and removal, zero-change mixed-batch preflight, and REST/MCP calls for
all four tools. Native metadata and actual descendant state are asserted, rather than inferred
from mock role flags. Inspector 2.8.0 compares membership rows with native state and checks
the allowed_all writer catalog/schema and management capability grants.

EVID-033-LIVE-020: native scenario and Inspector pass. Membership deletion clears the disposable
project default assignee and category assignee; existing issue assignment remains unchanged.
The guarded helper creates disposable projects/roles, uses existing ordinary users, and verifies
that no task projects/roles remain after teardown. Existing grants/memberships are not changed.
Full current offline regression passes 1086 cases and preserves original 001..010 criteria,
including prep-019 uncertainty and batch stopping. AC-001..010 therefore have combined offline
and native evidence. See the [current ledger](../../testing/evidence/current-catalog-acceptance.md) for commands,
execution results and narrower observations. Current final status: **complete**. This is not
operational release approval or a promise that public role metadata exposes every restriction.

Next action: authorize scenario 011 startup/Inspector and resulting-state checks in the owned
7.0.2 synthetic environment, including inherited and protected roles, descendant/default-assignee
effects, reconciliation and task-owned cleanup. The container observed as 6.0.5 cannot supply
this acceptance. Offline coverage ownership and reproducible commands are recorded in section 7.
