# prep-013-caller-tool-discovery: Filter tool discovery for each caller

> Writer admission update (2026-10-13): pinned-key and user ID admission checks
> are retired. Earlier requirements and evidence below describe historical behavior.
> See [current configuration](../../configuration.md#separate-writer-deployment).

## 1. Task identity and status

| Field | Value |
|---|---|
| Task ID | prep-013-caller-tool-discovery |
| Assigned capability | Discover relevant tools without exposing another caller's capability context |
| Type / access / destructive effects | Shared MCP discovery prerequisite / discovery is read-only, invocation remains mixed / None from discovery |
| Status | blocked |
| Dependencies | [prep-010](prep-010-permission-session-contract.md) adapter contract; [prep-011](prep-011-multi-user-writer-auth.md); [prep-012](prep-012-project-resource-authorization.md) |
| Related tasks | [Roadmap](../multi-user-writer-authorization.md); [dashboard](../index.md); prep-014 |
| Target version | Redmine 7.0.2; FastAPI-MCP 0.4.0; MCP SDK 1.30.0 |
| Last updated | 2026-10-05, Codex |
| Progress summary | Personal-writer raw discovery handler, copied caller results and immutable superset schema cache implemented; static checks pass |
| Blocker / next action | Execute DISC-001 through DISC-007 in the assigned separate prep-014 verification stage |

## 2. Discovery and evidence

Current `register_mcp` selects one operation list at startup, validates generated tools and routes,
sets annotations, then mounts HTTP. Installed FastAPI-MCP 0.4.0's list handler returns shared
`self.tools`; its invocation handler reads request context and forwards allowed headers.
The repository starts a stateful MCP SDK manager and uses version-specific private transport
members. A safe handler override must be contained in the repository adapter, not site-packages.
Sources checked 2026-10-05: `mcp/registration.py`, `catalog.py`, `annotations.py`, installed
FastAPI-MCP `server.py:146-184`, `uv.lock`, and [roadmap upstream evidence](../multi-user-writer-authorization.md#baseline-evidence-and-limitations).
Permission APIs are partial; discovery cannot promise success for every project/payload.
Initial working tree was clean; preserve prior catalog and acceptance records.

Decisions: no new tools or mandatory project argument to `tools/list`; preserve all generated
schemas, stable operation IDs and write annotations. Read tool discovery remains compatible.

## 3. Requirements

| ID | Required observable behavior |
|---|---|
| REQ-001 | A caller's tools never exceed the deployment catalog or operation admission limits |
| REQ-002 | Discovery uses only that caller's capability evidence; global tool registry remains immutable |
| REQ-003 | Discovery distinguishes candidates from guaranteed permission for a concrete target |
| REQ-004 | Direct calls to hidden tools still pass the same authoritative authorization boundary |
| REQ-005 | Repeated discovery refreshes permissions; session/header isolation and existing schemas are preserved |

Example: caller A has `add_issues` in one visible project and sees `create_issue` as a candidate.
Caller B has complete evidence of no applicable create permission and does not see it. Caller A
calling into another project is still checked there. Unknown public-project coverage must not be
misrepresented as definitive denial.

## 4. Public contract and technical specification

### Discovery interface

MCP `tools/list` is extended; no REST endpoint or new operation ID is introduced. Authentication
uses the existing single key header, refreshed per request. No key/user/project tool argument.
Response remains standard MCP tool definitions from the validated deployment superset.

Selection algorithm, preserving canonical catalog order:

1. Authenticate caller and enforce session binding before accessing MCP session state.
2. Reader deployment returns its existing read catalog only.
3. Writer starts with read tools plus enabled deployment write operations.
4. For personal-key mode, exclude all writes for a caller outside a nonempty write admission list.
5. Use prep-012's capability resolver for each remaining write: keep conditional/unknown
   candidates; omit only proven denial across all applicable contexts. One conditional or unknown
   context prevents a global denial. No visible membership is not proof of no public access.
6. `upload_attachment` uses the reviewed global upload rule, rather than an invented project rule.
7. Return a request-local list without modifying global tools, schemas, annotations, or operation map.

Pinned-key deployments keep existing discovery behavior. Existing read tools remain in the list
for authenticated callers. Descriptions must explain that availability depends on the target and
Redmine's final check, without exposing internal configuration or another caller's project data.

Discovery is a candidate list. Exact workflow/field/tracker eligibility is resolved during
invocation by the same caller-key Redmine request. Clients may cache discovery; no proactive
`list_changed` notification is promised in this phase. A new `tools/list` refreshes evidence,
and every invocation rechecks current access regardless of any cached list. Empty candidate write
set is a valid result, not a connection failure.

### Invocation and errors

A guessed or previously discovered hidden tool cannot bypass REST authorization. Application
known denial returns the existing sanitized permission error with no mutation; resource/upstream
errors retain existing mappings. Missing/invalid key and session mismatch are transport rejection.
Role lookup 403/404 is unknown metadata; timeout/malformed/429 errors propagate sanitized failure
without leaking a previous caller's list or silently returning stale grants.

List pagination follows the existing adapter/SDK contract; no new cursor contract is invented.
No Redmine mutation happens during discovery. Invocation preserves existing write receipts,
no retries, uncertain outcome reconciliation and state/read-back semantics.

### Adapter integration blocker

prep-010 must specify exact SDK handler registration, authenticated request-context retrieval,
context lifetime, interaction with the already-generated FastAPI-MCP operation map, and the
session binding hooks from prep-011. Add startup validation of the complete generated superset;
do not require each filtered list to equal that superset. Prevent unhandled missing context from
falling back to a global privileged list. Avoid a dependency upgrade unless source proves the
locked stack cannot support the required boundary; then revise `pyproject.toml` and `uv.lock`
together with compatibility justification before coding.

Specification exit: resolved by the [prep-010 contract review](../../reviews/prep-010-contract-review.md).
Register a raw ListToolsRequest handler, initialize the superset schema cache once, and reuse
the SDK session owner boundary via authenticated scope. No dependency upgrade is required.

## 5. Implementation plan

| Step | Concrete ownership | Verification handoff |
|---|---|---|
| 1 | Finalize adapter/session design through prep-010 | DISC-001 |
| 2 | `mcp/registration.py` or contained new MCP adapter: request-local list handler | DISC-002/003 |
| 3 | `mcp/catalog.py`: immutable deployment superset validation and scoped selection | DISC-004 |
| 4 | Preserve forwarding and REST invocation checks; reuse prep-012 resolver | DISC-005/006 |
| 5 | Tool reference, architecture, manual verification and changelog: candidate semantics and refresh | DISC-007 |
| 6 | Static checks during coding; verification handed off to prep-014 | No unrequested tests |

Dependency changes are not preauthorized by availability; resolve the minimal technical choice
through prep-010. Do not edit installed packages or implement separate business logic inside MCP.

## 6. Acceptance criteria and traceability

| Criterion | Requirement | Observable result | Scenarios |
|---|---|---|---|
| AC-001 | REQ-001 | Reader and writer/user ceilings respected, including empty operations | DISC-004 |
| AC-002 | REQ-002 | Concurrent lists differ correctly without changing shared registry | DISC-002/003 |
| AC-003 | REQ-003 | Known denial omitted; conditional/unknown candidates retained truthfully | DISC-002/007 |
| AC-004 | REQ-004 | Hidden/guessed/cached tool calls cannot bypass authorization | DISC-005 |
| AC-005 | REQ-005 | Key/session changes, role revocation, missing context and upstream failure are isolated | DISC-003/006 |

All results pending; source-level adapter findings are not runtime evidence.

## 7. Test plan and execution record

Plan only; use the existing credential-free MCP client/ASGI baseline when separately authorized.

| Scenario | Expected result | Mode |
|---|---|---|
| DISC-001 | Reviewed handler/context/session contract is implementable at locked versions | Source review |
| DISC-002 | Two callers, A/B permissions, no memberships, admin, inherited roles, partial metadata | Offline MCP; synthetic |
| DISC-003 | Concurrent discovery/invocation, missing context, reused session ID and changed key | Offline MCP |
| DISC-004 | Immutable registry, stable names/order/schemas/annotations and all deployment ceilings | Offline MCP |
| DISC-005 | Hidden or cached tool invoked directly is rechecked and denied before mutation when forbidden | Offline REST/MCP; synthetic |
| DISC-006 | Role revoked then discovery/call refreshed; role endpoint 403/404/429/malformed/timeout | Offline; synthetic |
| DISC-007 | Client documentation accurately describes candidates and reconnect/refresh limitations | Review; opt-in Inspector |

| Evidence | Procedure | Actual / status |
|---|---|---|
| EVID-001 | prep-010 handler/cache review; installed Ruff lint/format, mypy src, AST architecture and git diff --check; 2026-10-05 | Pass / runtime evidence pending |
| EVID-002 | Authorized selected DISC scenarios against offline baseline | Not run / pending |
| EVID-003 | Authorized two-user Inspector and marked synthetic permission/state checks | Not run / pending |

## 8. Implementation and review record

Implemented on 2026-10-05: `mcp/discovery.py` validates the reviewed SDK cache shape, seeds the
deployment schema superset once and installs a raw ListToolsRequest handler. The handler reads
the authenticated original Request/AuthContext, applies personal writer admission, reuses the
request-local capability resolver and returns deep copies in canonical order. Known denied
writes are hidden; conditional/unknown candidates carry a target-permission description.
The original invocation handler, REST forwarding and operation map remain intact, so hidden or
cached calls retain authoritative checks. Missing context fails closed and upstream errors are
sanitized. Reader and pinned-key registrations retain existing discovery. No installed package
patched or dependency upgraded; the SDK was already pinned in prep-011.
Ruff lint/format pass repository-wide (188 files); mypy src passes (105 modules); AST import
boundaries/cycles and git diff --check pass. Formatting affected only the assigned new adapter.
Final source/diff review confirms no per-caller mutation of the global tools or schema registry.
No tests/fixtures, startup, Inspector or live checks run in this coding stage. DISC-001 through
DISC-007, concurrency and revocation evidence remain assigned to prep-014.

## 9. Completion and handoff

- [x] Adapter/session integration contract reviewed.
- [x] Caller discovery and immutable registry implemented.
- [x] Direct-call authorization and credential isolation preserved by source inspection; runtime evidence pending.
- [ ] Static checks and separately authorized acceptance evidence pass.
- [ ] Documentation, final diff, task and dashboard synchronized.

Final status: blocked - implementation finished; testing pending. Next action: execute the
separately assigned prep-014 verification stage, including direct-call and concurrent-session checks.
