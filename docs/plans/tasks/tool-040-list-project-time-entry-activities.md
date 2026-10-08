# tool-040: Discover project time-entry activities

## 1. Task identity and status

| Field | Value |
|---|---|
| Task ID | tool-040-list-project-time-entry-activities |
| Assigned capability | Let a caller choose an activity by name before logging time on an issue |
| Type / access | Add tool / read |
| Destructive effects | None |
| Status | complete (testing waived by user) |
| Dependencies | Existing project reader and bounded GET client; accepted prep-020 catalog baseline; prep-002/016/017/018 infrastructure for later verification |
| Related tasks | [tool-041](tool-041-create-time-entry.md), [tool-003](tool-003-get-project.md), [tool-031](tool-031-list-my-project-capabilities.md) |
| Target Redmine version | Pinned 7.0.2 source inspected; new runtime acceptance pending |
| Last updated | 2026-10-08, Codex |
| Progress summary | Implementation finished; static checks pass; user explicitly waived testing on 2026-10-08 and directed TOOL-041 continuation |
| Blocker | None under the user's testing waiver; runtime behavior remains unverified |
| Next action | Continue TOOL-041 as assigned; revisit TOOL-040 verification only in a future explicit assignment |

## 2. Discovery and evidence

### Client outcome and repository baseline

The caller requested eight hours on each issue found with tag `notification`. When no native
default is available, creation needs an activity ID. Existing project/version/category and
global reference tools do not expose activities. A separate project catalog is independently
useful and avoids treating global enumeration IDs as the project's effective choices.

Use the existing `features/projects/` models, reader Protocol, service and router, and
`integrations/redmine/projects.py` adapter. `bootstrap.py` already wires this reader. Register
the operation in `auth/policy.py`, `mcp/catalog.py` and the project read-capability rules.
Preserve `get_project` and all existing schemas. Instructions are `AGENTS.md`, `CONTRIBUTING.md`,
[workflow](../../workflows/redmine-tools.md) and [template](../../templates/redmine-tool-task.md).
All documents are English; commands are Git Bash. Planning authorizes no tests or live calls.
The working tree was clean at discovery. Historical TOOL-037/038/039 identities are reserved;
this task uses a fresh ID. Existing tool and writer acceptance is baseline evidence only.

Coding was explicitly assigned on 2026-10-08. Its starting working tree contained the earlier
planning changes to `docs/plans/index.md` and the untracked TOOL-040/041 documents. Those plans
were preserved; TOOL-041 remains unimplemented. `bash scripts/doctor.sh` confirmed required
Git Bash, Git, Python 3.13 and uv prerequisites without reading credentials or installing tools.

### Upstream evidence

Exact files were read from the existing local archive of the official
[7.0.2 release](https://www.redmine.org/releases/redmine-7.0.2.tar.gz), without executing Ruby.
The target is pinned in `deploy/compose.test.yaml`.

| Source URL or versioned source | Date verified | Version | Behavior / permission | Evidence or limitation |
|---|---|---|---|---|
| [Projects helper](https://raw.githubusercontent.com/redmine/redmine/7.0.2/app/helpers/projects_helper.rb), `render_api_includes` | 2026-10-08 | 7.0.2 | Project detail include `time_entry_activities`; requires `view_time_entries` | Expansion returns activity ID/name and is omitted when permission fails |
| [Project model](https://raw.githubusercontent.com/redmine/redmine/7.0.2/app/models/project.rb), `activities` | 2026-10-08 | 7.0.2 | Active shared and project activities, excluding overridden parent IDs | A project override can have a different ID; inactive choices excluded |
| [Project API template](https://raw.githubusercontent.com/redmine/redmine/7.0.2/app/views/projects/show.api.rsb) | 2026-10-08 | 7.0.2 | Project detail calls `render_api_includes` | No default flag or pagination metadata for this expansion |
| [TimeEntryActivity model](https://raw.githubusercontent.com/redmine/redmine/7.0.2/app/models/time_entry_activity.rb) | 2026-10-08 | 7.0.2 | Defaults can depend on the caller's roles and project | Catalog must not claim that its first item is the caller's default |

These are source findings, not live verification. The previously observed localhost:3000
instance was 6.0.5; do not label future checks there as 7.0.2 acceptance.

| Client outcome / tool | Existing coverage | Access | Owner | Dependencies | Scope |
|---|---|---|---|---|---|
| Choose an active project activity by name | None | Read | TOOL-040 | Existing project reader | In scope |
| Log own time on one issue | Readers only | Write | TOOL-041 | Existing writer; TOOL-040 for named choices | Separate task |

### Questions and decisions

| ID | Decision | Blocking? | Resolution date |
|---|---|---|---|
| DEC-001 | Use the project detail expansion, not global enumerations | No | 2026-10-08 |
| DEC-002 | Return ID/name only; do not infer active/default flags absent from the expansion | No | 2026-10-08 |
| DEC-003 | Missing expansion means unavailable; present empty array means no available choices | No | 2026-10-08 |
| DEC-004 | Creation does not require this read permission when a known ID or native default is used | No | 2026-10-08 |

## 3. Requirements

Intended callers resolve the issue's project through `get_issue` or `list_issues`, then select
an activity from that project's catalog. Scope covers discovery only. Activity administration,
global catalogs, role-default reconstruction and changes to existing `get_project` are deferred.

| ID | User need and observable behavior | Prerequisites/constraints |
|---|---|---|
| REQ-001 | Return the selected visible project's active activity IDs and names | Positive numeric project ID; native project access |
| REQ-002 | Distinguish unavailable expansion from known empty choices | Preserve visibility observations |
| REQ-003 | Reject invalid input and malformed returned data without guessing | Strict IDs and names; no write |
| REQ-004 | Expose REST/MCP discovery and conditional project capabilities | Read authorization; native `view_time_entries` |

Synthetic example: project 2 returns activity 9, `Development`; a global parent activity 4
overridden in that project must not be substituted for 9. These IDs are illustrative.

## 4. Public contract and technical specification

### Tool and REST interface

| Area | Decision |
|---|---|
| New tool / operation ID | `list_project_time_entry_activities` |
| Purpose / exact description | List active time-entry activity IDs and names available to one visible project. Resolve the project from the issue or list_projects. Use a returned ID when logging time. Requires native View spent time permission for the expansion. Missing items are marked unavailable; a known empty list means no available activities. This catalog does not identify the caller's default or grant permission to log time. |
| REST | `GET /api/v1/projects/{project_id}/time-entry-activities` |
| Authentication | Existing per-user Redmine key and `require_read_access` |
| MCP exposure | Explicit read catalog entry; read-only and non-destructive annotations |
| Capability rule | Project-scoped necessary `view_time_entries`; native access/module restrictions remain conditional |

### Inputs

| Field/location | Type | Required/default | Validation | Omitted/null/empty | Mapping |
|---|---|---|---|---|---|
| project_id / path | Integer | Required | Strict positive ID in service; REST follows repository path validation | Rejected | `projects/{id}.json` |

No pagination or default-selection input. Unsupported arguments follow the current shared
REST/MCP unknown-input policy; do not add a new global admission policy.

### Outputs and mapping

`Collection[ProjectTimeEntryActivity]`, using the existing visibility envelope. Each item has a
strict positive integer `id` and a nonempty string `name`. Send one bounded
`GET projects/{project_id}.json?include=time_entry_activities`. Validate `project` and its ID
before reading the expansion. A missing expansion returns `items=[]` with
`{"path":"/items","state":"not_returned"}`; an explicit empty array returns `items=[]`
without that observation. Explicit null, nonarrays, invalid items or duplicate IDs are malformed
upstream data, not a known empty catalog. Preserve upstream order without promising sorting.
No total, pagination, default or role inference. Return HTTP 200 / structured MCP result.

```json
{
  "items": [{"id": 9, "name": "Development"}],
  "visibility": {"scope": "requesting_redmine_user", "observations": []}
}
```

Existing project routes and outputs remain compatible.

### Errors

| Scenario | Detection | REST status / code | MCP / retry behavior |
|---|---|---|---|
| Invalid ID | Route/service | 422 / `invalid_parameters` | Existing error envelope; no catalog request |
| Missing/invalid key | Existing authentication | 401 / `invalid_credentials` | Existing envelope |
| Forbidden/missing project | Native project GET | 403 / `access_denied`, 404 / `resource_not_found` | Do not expose hidden project details |
| Missing expansion | Adapter | 200 / unavailable observation | No permission claim; no fallback scan |
| Malformed expansion or wrong project ID | Adapter | 502 / `upstream_response` | Existing error envelope |
| Timeout, budget, size, pool, rate limit or other GET failures | Shared bounded GET transport | Existing documented read status/code | Existing bounded eligible GET retries only |

### Write semantics

N/A - read-only. No state changes, enumeration updates or administrative setup.

Specification exit check: all material public-contract decisions resolved by pinned source.

## 5. Implementation plan

| Step | Change | Files/components | Depends on | Planned verification |
|---|---|---|---|---|
| 1 | Add ID/name model and reader method | `features/projects/models.py`, `ports.py`, exports | Existing project reader | TOOL-040-001/002 |
| 2 | Map bounded project expansion and visibility | `integrations/redmine/projects.py` | 1 | TOOL-040-002/003 |
| 3 | Add service method and authenticated route | `features/projects/service.py`, `router.py` | 1-2 | TOOL-040-001/004 |
| 4 | Register read operation and capability rule | `auth/policy.py`, `mcp/catalog.py`, `features/users/capability_rules.py` | 3 | TOOL-040-004 |
| 5 | Document catalog and writer workflow | `docs/tool-reference.md`, `docs/manual-verification.md`, `CHANGELOG.md` | 4 | Manual source/prose review |
| 6 | In a separately authorized stage, add and execute test scenarios | `tests/unit/`, `tests/integration/`, selected `tests/e2e/` | Implementation | TOOL-040-001..005 |

No dependency, lockfile, runtime configuration or Redmine server changes planned. Existing
`bootstrap.py` project-reader wiring is reused. Review follows planning; coding and testing
remain separately assigned stages.

## 6. Acceptance criteria and traceability

| Criterion | Given | When | Then |
|---|---|---|---|
| AC-001 | Visible project with shared/overridden active choices | List activities | Exact effective IDs/names returned; no invented defaults |
| AC-002 | Empty or omitted expansion | List activities | Known empty and unavailable remain distinguishable |
| AC-003 | Invalid input or malformed upstream data | Invoke | Safe existing error, no guessed values |
| AC-004 | Authenticated REST/MCP caller | Discover/invoke | Stable schema/annotations and conditional project rule; existing tools preserved |

| Requirement | Criteria | Verification | Evidence/result |
|---|---|---|---|
| REQ-001 | AC-001 | TOOL-040-002/005 | Not run; waived by user |
| REQ-002 | AC-002 | TOOL-040-003/005 | Not run; waived by user |
| REQ-003 | AC-003 | TOOL-040-001/003/004 | Not run; waived by user |
| REQ-004 | AC-004 | TOOL-040-004/005 | Not run; waived by user |

## 7. Test plan and execution record

### Scenario plan

Use the existing offline baseline, fake settings, HTTPX MockTransport, lifespan-managed ASGI and
MCP SDK scenarios. New tests, execution and live setup require separate authorization.

| Scenario ID | Criteria | Layer | Setup/input and expected result | Mode |
|---|---|---|---|---|
| TOOL-040-001 | AC-003 | Unit/service | Reject invalid IDs before catalog access; valid ID forwarded | Offline |
| TOOL-040-002 | AC-001 | Adapter | Exact URL/include; shared and project override IDs/names; preserve order | Offline |
| TOOL-040-003 | AC-002/003 | Adapter | Present empty, missing expansion, null, bad wrapper/ID/name, duplicate ID, timeout and bounded response errors | Offline |
| TOOL-040-004 | AC-003/004 | REST/MCP | Auth, discovery, schema, annotations, invocation/errors, capability rules and existing-catalog compatibility | Offline |
| TOOL-040-005 | AC-001/002/004 | Owned Redmine 7.0.2 + Inspector | Populated/empty project, inactive and overridden choices, permitted vs no-view account, forbidden project; compare native source/API, cleanup | Opt-in live |

Pagination and write outcomes are N/A. Inputs, exact mapping, empty/malformed/error responses,
auth, compatibility and MCP behavior are covered above. Setup may create task-owned project
activity fixtures only within the later explicitly authorized marked synthetic environment.
No modifications of the user's existing Redmine server are required by this plan.

### Execution evidence

| Evidence ID | Planned command/procedure | Scenarios | Expected | Actual/status/date |
|---|---|---|---|---|
| TOOL-040-EVID-001 | `uv run --frozen --no-sync ruff check .`; `uv run --frozen --no-sync ruff format --check .` | Repository lint/format | No introduced findings | Seven existing lint findings and one existing unformatted file outside task scope; failed, 2026-10-08 |
| TOOL-040-EVID-002 | `uv run --frozen pytest tests/unit tests/integration -q` in authorized testing stage | TOOL-040-001..004 | Relevant new and existing contracts pass | Not run; waived by user, 2026-10-08 |
| TOOL-040-EVID-003 | Selected task-owned live E2E and Inspector on marked pinned 7.0.2 | TOOL-040-005 | Native parity, permissions and cleanup pass | Not run; waived by user, 2026-10-08 |
| TOOL-040-EVID-004 | Scoped Ruff commands below | Nine changed runtime files | Lint/format pass | All checks passed; nine files already formatted; passed, 2026-10-08 |
| TOOL-040-EVID-005 | `uv run --frozen --no-sync mypy src` | Runtime typing | Pass | No issues in 124 source files; passed, 2026-10-08 |
| TOOL-040-EVID-006 | `git diff --check`; manual runtime/docs diff inspection | Whitespace/architecture/contracts | Clean task diff | Passed, 2026-10-08; test files and unrelated Ruff-failing files unchanged |
| TOOL-040-EVID-007 | `bash scripts/doctor.sh` | Prerequisites | Required tools available | Passed, 2026-10-08; no credential read or installation |

Exact scoped static commands executed from Git Bash:

```bash
uv run --frozen --no-sync ruff check src/redmine_mcp/features/projects/models.py src/redmine_mcp/features/projects/ports.py src/redmine_mcp/features/projects/__init__.py src/redmine_mcp/features/projects/service.py src/redmine_mcp/features/projects/router.py src/redmine_mcp/integrations/redmine/projects.py src/redmine_mcp/auth/policy.py src/redmine_mcp/mcp/catalog.py src/redmine_mcp/features/users/capability_rules.py
uv run --frozen --no-sync ruff format --check src/redmine_mcp/features/projects/models.py src/redmine_mcp/features/projects/ports.py src/redmine_mcp/features/projects/__init__.py src/redmine_mcp/features/projects/service.py src/redmine_mcp/features/projects/router.py src/redmine_mcp/integrations/redmine/projects.py src/redmine_mcp/auth/policy.py src/redmine_mcp/mcp/catalog.py src/redmine_mcp/features/users/capability_rules.py
```

Repository Ruff findings are six I001 import findings in `api/dependencies.py`,
`common/read_budget.py`, `features/attachments/router.py`, `integrations/redmine/retry.py`,
`integrations/redmine/transport.py` and `mcp/read_limits.py`, plus E501 and formatting in
`features/users/capability_service.py`. These files have no task diff. No unrelated fixes applied.

Limitations: static checks and source/diff inspection only. No runtime version probe, fixtures,
test creation/modification/execution, startup, Inspector or live calls performed. The full
`scripts/check.sh` wrapper was inspected but not run; its architecture-script execution and
automatic dependency synchronization are outside this static-only coding stage. Existing
historical acceptance does not accept this new operation. No build/dependency change required.

## 8. Implementation and review record

- Changes made: strict ProjectTimeEntryActivity model/export, ProjectReader Protocol method,
  service validation, authenticated GET route, bounded native project expansion mapping,
  missing-field visibility, duplicate rejection, read allowlist and project capability rule.
  Existing bootstrap project-reader wiring and shared GET transport/annotations are reused.
- Plan deviations: description says "Use a returned ID when logging time" so the current reader
  does not imply the separately planned create_time_entry writer is already available.
- Quality results: TOOL-040-EVID-004/005/006/007 pass. Repository-wide Ruff findings are recorded
  separately in TOOL-040-EVID-001; no task-file lint/format findings remain.
- Tests/startup/Inspector: TOOL-040-001..005 and EVID-002/003 remain unexecuted; user waived testing
  on 2026-10-08 and directed TOOL-041 continuation.
- Documentation updated: tool reference, manual verification, changelog, README catalog count,
  architecture count/rule and synchronized task/dashboard. Catalog is now 18 reads and 15 writes;
  historical acceptance numbers retain their original dates and do not include this operation.
- Diff review: router -> service -> Protocol -> gateway preserved; native include parameter,
  project identity, missing-vs-empty behavior and strict item validation inspected. No credentials,
  configuration, dependencies, tests, live state or unrelated runtime changes.
- Testing handoff: implement TOOL-040-001..005. Update the new operation's arguments in
  `tests/integration/test_current_tools.py` READ_ARGUMENTS and the all-reader argument maps in
  `tests/integration/test_reader_contracts.py`; extend project reader fakes where Protocol
  conformance is required. Add populated/missing/empty/malformed/duplicate adapter fixtures,
  native error/budget cases, capability and MCP discovery/schema/annotation cases. Execute owned
  7.0.2 permission/inactive/override fixtures and Inspector parity only when authorized.
- Remaining blocker: none under the explicit user waiver; scoped static success is not runtime acceptance.

## 9. Completion and handoff

- [x] Required behavior implemented.
- [ ] Every requirement has passing acceptance evidence.
- [ ] Relevant automated tests and repository checks pass.
- [ ] Required live verification completed, including permission boundaries and owned cleanup.
- [x] Public documentation reflects implemented behavior.
- [x] No unresolved decision changes the specified behavior.
- [x] Implementation diff reviewed and task/dashboard synchronized.

Final status: **complete under the user's explicit testing waiver**. Outcome: the activity
reader is present in source and the explicit REST/MCP catalog, with required runtime typing and
scoped lint/format checks passing. Deployment/startup and runtime acceptance were not performed.
On 2026-10-08 the user directed "skip testing for 040, continue implement 041". This overrides
the normal testing exit criteria for TOOL-040 only and permits continuation; it is not passing
acceptance evidence. TOOL-040-001..005 and EVID-002/003 remain unexecuted and are waived for this
handoff. The unchecked testing items above accurately retain that limitation.
Next action: implement TOOL-041 as separately assigned. Future testing requires explicit assignment.
The unrelated repository Ruff findings remain separately recorded and were not changed.
