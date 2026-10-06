# tool-032: Create project Target versions

## 1. Task identity and status

| Field | Value |
|---|---|
| Task ID | tool-032-create-project-version |
| Assigned capability | Create sprint-01 in the selected Demo API project and receive its version ID |
| Type / access | Add tool / write |
| Destructive effects | None intended; creates one version, with native Redmine creation hooks |
| Status | blocked |
| Dependencies | Existing project reader; prep-007 and prep-010-013 writer implementations; prep-016-018 testing infrastructure |
| Related tasks | [tool-007](tool-007-list-project-versions.md), [tool-031](tool-031-list-my-project-capabilities.md) |
| Target Redmine version | 7.0.2; this operation's runtime acceptance pending |
| Last updated | 2026-10-06, Codex |
| Progress summary | Implementation and offline verification finished; 581 offline cases pass; live acceptance pending |
| Next action | Separately authorize TOOL-032-008 on the isolated marked 7.0.2 environment |

## 2. Discovery and evidence

The existing `list_project_versions` discovers versions but cannot create them. This task adds
one operation through the existing router -> service -> dedicated Protocol port -> gateway flow.
Project-file wiring and the reader Version model remain compatible. Existing restricted writer,
caller identity, request-local project capabilities, single-attempt transport, and bounded reads
are reused. Runtime prerequisites are configured rather than enabled by this assignment.

Repository instructions require English Markdown, Git Bash commands, and separately authorized
testing. The user explicitly authorized this plan's code and documentation, including creation
of this task document and dashboard row. The task file did not exist before implementation;
it is populated from the approved conversation plan. Preserve unrelated untracked
`docs/team-planning/` files. No credentials or local runtime configuration were read or changed.

### Upstream evidence

Authoritative sources inspected during planning on 2026-10-06:

| Source | Version | Finding |
|---|---|---|
| [VersionsController](https://raw.githubusercontent.com/redmine/redmine/7.0.2/app/controllers/versions_controller.rb) | 7.0.2 | POST projects/:project_id/versions.json creates one version; 201 renders the version; validation rejection is 422 |
| [Version model](https://raw.githubusercontent.com/redmine/redmine/7.0.2/app/models/version.rb) | 7.0.2 | Name presence, maximum 60, case-sensitive project-scoped uniqueness; description maximum 255; valid effective/due date |
| [Permissions](https://raw.githubusercontent.com/redmine/redmine/7.0.2/lib/redmine/preparation.rb) | 7.0.2 | Creation uses manage_versions; version index/show use view_issues |
| [Version API template](https://raw.githubusercontent.com/redmine/redmine/7.0.2/app/views/versions/show.api.rsb) | 7.0.2 | Version ID, project, name, description, status, due_date, and sharing are returned |

The configured synthetic target is pinned 7.0.2. The dashboard records a separate shared 6.0.5
instance; acceptance must use the isolated marked 7.0.2 environment. Source inspection is not
runtime evidence. Configured Redmine plugins/hooks and required version custom fields can still
affect upstream validation; custom field input is excluded from this first version.

### Decisions

| ID | Decision | Blocking? |
|---|---|---|
| DEC-001 | User selected basic sprint creation: open status and no sharing | No |
| DEC-002 | User requested existing version data plus an explicit duplicate error | No |
| DEC-003 | Preserve existing fields on duplicates; do not update or rename | No |
| DEC-004 | Read permission is optional for creation; unreadable duplicates keep validation errors | No |
| DEC-005 | Coding-only assignment excludes test edits, execution, startup, Inspector, and live calls | Acceptance pending |
| DEC-006 | On 2026-10-06 the user requested testing for this feature; add and run offline unit/REST/MCP checks. Live Redmine verification remains a separate assignment | No |

## 3. Requirements

Intended callers create a Target version in an already selected project. Resolve the numeric
project ID through `list_projects`; names are not project identifiers. In scope: one open,
unshared version, optional description/date, duplicate reporting, writer authorization, and
explicit write receipts. Excluded: update/delete, sharing/status selection, custom fields,
wiki settings, automatic issue assignment, and project creation.

| ID | Required observable behavior |
|---|---|
| REQ-001 | Create one project-owned version with status open and sharing none |
| REQ-002 | Accept name and optional description/due date with early validation |
| REQ-003 | Return a readable existing same-project version with an error; preserve existing metadata |
| REQ-004 | Enforce deployment operation/user gates, identity, and target permission |
| REQ-005 | Separate acceptance, independent verification, and uncertainty; never retry automatically |

## 4. Public contract and technical specification

### Tool and inputs

- Operation: `create_project_version`.
- REST: `POST /api/v1/projects/{project_id}/versions`, guarded by `require_write_access`.
- Description: Create an open, unshared Target version in a selected project. Requires the
  restricted writer and Manage versions permission. Returns an existing readable version with
  an explicit error when creation is rejected and that project already contains the same name.
  Reports acceptance separately from verification; reconcile uncertain outcomes before retrying.
- MCP hints: readOnlyHint=false, destructiveHint=false, idempotentHint=false, openWorldHint=true.
- Existing pinned-key and personal-key authentication apply. In personal mode authorize a
  WriteIntent for the actual destination project with manage_versions; incomplete evidence
  remains unknown and Redmine retains final authorization. No additional view_issues creation gate.

| Input | Validation and defaults | Upstream mapping |
|---|---|---|
| project_id | Positive numeric path ID | projects/{project_id}/versions.json |
| name | Required string, 1-60 characters, nonblank; preserve case/whitespace | version.name |
| description | Optional string, maximum 255; empty allowed; omitted/null omitted | version.description |
| due_date | Optional valid YYYY-MM-DD calendar date; datetime/empty rejected; omitted/null omitted | version.due_date |

Unknown body fields are forbidden, including status and sharing. POST one JSON version object
with supplied non-null fields and explicit `status=open`, `sharing=none`. No pagination inputs,
sorting, or expansions apply.

Example MCP input:

```json
{"project_id": 10, "name": "sprint-01", "description": "First sprint", "due_date": "2026-10-20"}
```

### Result

`CreateProjectVersionResult` contains outcome (`accepted|existing|uncertain`), nullable
upstream_accepted, nullable positive resource_id, verification (`matched|mismatch|unavailable`),
nullable observed_version, and nullable error. `ProjectVersionObservation` extends the existing
Version shape with required sharing. Preserve the reader's Version contract.

Structured receipts return REST HTTP 200 and the same MCP result. `error` is null for accepted
or uncertain writes. A duplicate returns existing resource data inside a normal structured MCP
result with a non-null application-level error, not a thrown MCP error envelope:

```json
{
  "outcome": "existing",
  "upstream_accepted": false,
  "resource_id": 123,
  "verification": "unavailable",
  "observed_version": {
    "id": 123,
    "name": "sprint-01",
    "project": {"id": 10, "name": "Demo API"},
    "status": "open",
    "sharing": "none",
    "description": "",
    "due_date": null
  },
  "error": {
    "code": "version_already_exists",
    "message": "Creation was rejected; a version with this name already exists. The existing version is returned. Supplied fields were not applied."
  }
}
```

### Errors and write semantics

| Scenario | Behavior |
|---|---|
| Invalid caller input | Existing sanitized REST 422 / MCP validation error, before mutation |
| Missing/invalid authentication | Existing REST 401 / MCP authentication handling |
| Writer disabled, excluded operation/user, or denied permission | Existing REST 403 / MCP tool error |
| Missing/forbidden project or rejected credential | Preserve existing upstream mappings and safe errors |
| Upstream 422 | One bounded best-effort project version lookup; exactly one same-project exact-name match returns existing plus error |
| Upstream 400 | Preserve sanitized validation error; do not attempt duplicate recovery |
| Duplicate lookup unreadable, absent, malformed, or ambiguous | Preserve original validation rejection |
| Valid 201 | Capture ID, independently GET versions/{id}.json, compare project and supplied/fixed fields |
| Read-back failure or unobserved requested field | Preserve acceptance; verification unavailable unless another observable mismatch is established |
| Dispatched timeout, unexpected success status, unusable creation response | Uncertain receipt; retain upstream_accepted=true if 201 was seen |
| Other transport/upstream failures | Reuse existing safe errors and pre-dispatch behavior |

Validate the full duplicate collection and its count before selecting a match. Duplicate IDs
or multiple matches are unreliable. Exclude shared versions whose owning project differs.
Do not parse or expose upstream validation messages. Keep the original 400/422 status internally
in a typed ApplicationError subclass; its public status/message stay unchanged.

Writes have one attempt, no idempotency guarantee, no rollback, and no concurrency guarantee.
A failed read cannot prove a preceding write failed. Do not infer creation from a name lookup
after timeout; callers reconcile using list_project_versions before retrying. Native creation
hooks remain upstream behavior. Verification and cleanup use only task-owned IDs in the isolated
marked synthetic environment; an existing version returned as a duplicate is never cleanup-owned.

## 5. Implementation plan

1. Add request, observation, result, and duplicate-error models plus a dedicated creator port.
2. Implement RedmineProjectVersions using bounded reads and the single-attempt writer.
3. Add the project service method and creator injection, preserving existing project-file wiring.
4. Add the writer route, stable allowlist entry, typed write operation, manage_versions mapping,
   and project-target capability resolution. Existing catalog/annotation code derives its new hints.
5. Document the tool, configuration opt-in, manual scenarios, changelog, and dashboard status.
6. Hand off test additions and runtime acceptance to a separately authorized assignment.

No dependencies, lockfile changes, database migrations, deployment changes, or test edits.
New service logic imports neither FastAPI nor HTTPX; the pre-existing status-only FastAPI import
in the touched project service was replaced with equivalent numeric statuses.

## 6. Acceptance criteria and traceability

| Criterion | Observable result | Requirements | Scenarios | Evidence |
|---|---|---|---|---|
| AC-001 | Returned ID and observed Redmine state match project/name/open/none and supplied fields | REQ-001/002 | TOOL-032-001/008 | Offline pass; live pending |
| AC-002 | Invalid input fails before mutation | REQ-002 | TOOL-032-002 | Offline pass |
| AC-003 | Readable duplicate returns existing data plus error without changes | REQ-003 | TOOL-032-003/004/008 | Offline pass; live pending |
| AC-004 | Writer and project permission boundaries prevent denied mutations | REQ-004 | TOOL-032-005/008 | Offline pass; live pending |
| AC-005 | Failure/timeout preserves acceptance and uncertainty with no retry | REQ-005 | TOOL-032-006/007 | Offline pass |
| AC-006 | Discovery, capabilities, annotations, readers, and project-file writes remain compatible | REQ-004 | TOOL-032-005 | Offline pass |

## 7. Test plan and execution record

The initial coding assignment did not write or run tests. The user subsequently authorized
testing on 2026-10-06. Added offline unit and REST/MCP integration tests; no live Redmine calls,
Inspector, seeding, resets, deployment, or credential changes are part of this follow-up.
Use existing fake settings/ports, HTTPX MockTransport, ASGI lifespan, and MCP SDK integration
infrastructure when separately authorized. Offline scenarios require no Docker or credentials.

| Scenario | Layer | Cases |
|---|---|---|
| TOOL-032-001 | Unit / offline integration | Exact JSON payload/defaults, valid response ID, independently matching read-back |
| TOOL-032-002 | Unit / REST / MCP | ID, blank/overlong name, description limits, valid/invalid dates, null/omission, extra fields |
| TOOL-032-003 | Offline integration | 422 plus exact own-project duplicate; metadata differs; no update and no second write |
| TOOL-032-004 | Offline integration | Case differences, shared version, absent/multiple matches, duplicate IDs, malformed counts/items, unreadable lookup; 400 does not recover |
| TOOL-032-005 | REST / MCP / capabilities | Deployment/user/operation gates, manage_versions target clause, conditional/unknown/denied evidence, annotations/discovery, project-file and reader compatibility |
| TOOL-032-006 | Offline integration | Malformed/missing creation payload/ID/project, unexpected success, dispatched timeout and single attempt |
| TOOL-032-007 | Offline integration | Read-back failure, missing optional fields, mismatch, 201 acceptance retention, pre-dispatch failures |
| TOOL-032-008 | Opt-in synthetic / Inspector | Ordinary authorized/denied callers, resulting state, duplicate unchanged state/count, create without view_issues, owned cleanup |

Later testing must account for the added writer catalog member and the dedicated project creator
dependency in any fixed-count/catalog and bootstrap expectations. Do not weaken existing tests.
Use the isolated marked 7.0.2 environment, not the shared 6.0.5 instance. No build is required
by dependency or packaging changes in this task.

| Evidence | Command / procedure | Actual result | Status |
|---|---|---|---|
| EVID-001 | bash scripts/doctor.sh | Required local development prerequisites available | Pass |
| EVID-002 | uv run --frozen --no-sync ruff check . | All checks passed, 2026-10-06 | Pass |
| EVID-003 | uv run --frozen --no-sync ruff format --check . | 223 files already formatted after test additions, 2026-10-06 | Pass |
| EVID-004 | uv run --frozen --no-sync mypy src | No issues in 112 source files, 2026-10-06 | Pass |
| EVID-005 | git diff --check and final source diff inspection | No whitespace errors; reviewed wiring, authorization, receipts, compatibility, and documentation; 2026-10-06 | Pass |
| EVID-006 | uv run --frozen --no-sync pytest tests/unit tests/integration -q | 581 passed, one dependency Pydantic deprecation warning, 165.13 seconds; 2026-10-06 | Pass |
| EVID-007 | TOOL-032-008 live Redmine / Inspector | Not run; separate live authorization required | Pending |

## 8. Implementation and review record

- Added models, creator Protocol, gateway, service, route, bootstrap injection, and exports.
- Registered operation and permission rules; discovery/capability reporting use existing gates.
- Updated tool reference, writer configuration example, manual guidance, changelog, and dashboard.
- Preserved writes-disabled defaults and local/deployed configuration, dependencies, and tests.
- Added internal RedmineWriteRejected upstream status so 400 cannot trigger 422-only recovery;
  public validation errors remain compatible.
- Initial static checks identified import formatting and a missing typed operation entry;
  these were corrected. Final lint, format, type, and diff checks passed as recorded above.
- Final review confirmed preserved project-file constructor compatibility, unchanged public
  validation error mappings, optional read permission, strict upstream observation conversion,
  single-attempt uncertainty, and caller-specific discovery through the existing registry.
  Only task-owned runtime/docs files changed; unrelated files and tests were preserved.
- At the end of the coding assignment, startup, Inspector, live state, acceptance, and automated
  checks remained pending. The follow-up below records the subsequently authorized offline evidence.

### Offline testing follow-up, 2026-10-06

- Added `tests/unit/test_project_versions.py` for date/name/optional input validation,
  invalid destination IDs, authorization before dispatch, and manage_versions capability evidence.
- Added `tests/integration/test_project_versions.py` for exact REST/MCP payloads, defaults/null,
  stateful duplicates, ambiguous/shared/malformed lookup, upstream errors, uncertain receipts,
  read-back mismatch/failure, credential and deployment/user gates, discovery and annotations.
- Extended the offline SyntheticRedmine fixture with version state and included the new operation
  in the existing writer success/reader-denial/permission-denial regression matrix.
- The first targeted run had 130 passing cases and three failures. One exposed a production
  contract bug: FastAPI-MCP 0.4 removed null from optional body field schemas. Restored this
  operation's request-model property schemas before SDK caching; the explicit-null MCP case
  remains a regression test. Two failures were fixed in the test helper, which now accepts the
  SDK's plain-text schema validation errors instead of assuming every error contains JSON.
- Full offline suite passed: 581 cases, including 80 new feature cases and four additions to
  the existing generic writer matrix. Ruff lint/format, mypy, and diff whitespace checks passed.
  One installed-dependency Pydantic deprecation warning remains. No tests were weakened or
  skipped to obtain a passing run. Do not treat mocks as live 7.0.2 acceptance.

## 9. Completion and handoff

- [x] Required code and documentation implemented.
- [ ] Every requirement has passing acceptance evidence.
- [x] Required static checks recorded as passing.
- [x] Separately authorized offline unit and integration verification completed.
- [ ] Live verification completed.
- [x] Final diff reviewed and task/dashboard synchronized.
- [x] No unresolved product decision changes the specified behavior.

Final status: **blocked - implementation and offline verification finished; live acceptance pending**.

Next action: separately authorize TOOL-032-008 to verify resulting 7.0.2 synthetic state and
permission boundaries, inspect the tool through Inspector, clean up only owned versions, and
update this record and dashboard. No deployment, operation enablement, commit, or real Demo API
version creation was performed by the coding or offline-testing assignments.
