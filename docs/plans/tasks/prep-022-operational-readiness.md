# prep-022-operational-readiness: Prepare a supportable pilot deployment

## 1. Task identity and status

| Field | Value |
|---|---|
| Task ID | prep-022-operational-readiness |
| Assigned capability | Let operators detect unhealthy service, trace writes, reproduce builds, and recover an owned deployment |
| Type / access | Shared operational prerequisite; health/telemetry reads and deployment infrastructure |
| Destructive effects | Later recovery rehearsal replaces data only in an explicitly owned disposable environment |
| Status | blocked |
| Dependencies | prep-019, prep-020, and prep-021 accepted; resolve DEC-001..004 before coding |
| Related tasks | [Dashboard](../index.md); original prep-009 final release review |
| Target Redmine version | Pinned 7.0.2; operational acceptance and recovery unexecuted |
| Last updated | 2026-10-07, Codex |
| Progress summary | Workstreams and acceptance goals planned; implementation contract awaits deployment/telemetry decisions |
| Next action | Resolve the four decision rows with the user, specify exact contracts, then assign phases one at a time |

## 2. Discovery and evidence

`api/health.py` always returns `{"status":"ok"}`. Compose uses that endpoint as a liveness
healthcheck. Runtime lifecycle owns clients and MCP startup/shutdown. Request/upstream logs
provide correlation, operation/method, status, and duration; they are not a complete writer audit.
No `.github` directory exists at planning time. Current testing guidance defers CI and coverage
thresholds; backup/restore helpers explicitly lack full recovery acceptance.

| Source / evidence | Reviewed | Finding / limitation |
|---|---|---|
| `api/health.py`, `lifecycle.py`, `mcp/registration.py`, `deploy/compose.yaml` | 2026-10-07 | Liveness, runtime ownership, localhost bindings, and separate writer |
| `observability.py`, `api/middleware.py`, `integrations/redmine/write.py` | 2026-10-07 | Safe request/timing logs; no complete outcome audit or metrics export |
| `scripts/check.sh`, `pyproject.toml`, `deploy/Dockerfile` | 2026-10-07 | Existing quality gate, locked package, non-root image; not a CI result |
| [Operations](../../operations.md), [testing roadmap](../../testing-roadmap.md) | 2026-10-07 | Hosting/CI/recovery decisions and acceptance remain deferred |
| `deploy/compose.test.yaml` | 2026-10-07 | Pinned native target, synthetic labels; no production recovery guarantee |

This task adds no Redmine API or permission. Deployment inventory and external platform choices
are not available in the review. Do not assume GitHub hosting, a cloud provider, a telemetry
service, a shared key for readiness, or ownership of the real Redmine database.

| Decision | Required resolution / recommended starting scope | Blocking? |
|---|---|---|
| DEC-001 | Pilot host, client, network boundary, TLS ownership, and release artifact; start with existing localhost Compose if it meets the user's pilot needs | Yes |
| DEC-002 | CI provider and explicit activation scope; recommend static/offline/package checks, with live E2E separately gated and no automatic deploy | Yes |
| DEC-003 | Metrics/audit sink, access, fields, retention, and process scope; recommend existing log collection before adding external infrastructure | Yes |
| DEC-004 | Recovery ownership/environment and acceptable outage/data-loss objectives; distinguish MCP restart/rollback from Redmine database/files restoration | Yes |

Resolve these in the future task assignment, then update this document and the dashboard to
`planned`. Record exact endpoints, schemas, settings/defaults, CI triggers/artifacts, and recovery
procedure before coding. A pending dependency alone is not the reason for the blocked status.

## 3. Requirements

In scope: readiness, safe writer audit, bounded operational metrics, CI/package reproducibility,
deployment/upgrade/rollback instructions, and owned recovery acceptance. Out of scope: new MCP
tools, public hosting activation, OAuth, per-user quotas, new databases, automatic deployment,
coverage-percentage thresholds, or restoring an external Redmine instance without explicit scope.

| ID | Required observable behavior | Constraint |
|---|---|---|
| REQ-001 | Operators distinguish process liveness from local application readiness and upstream availability | No new shared administrative key or credential exposure |
| REQ-002 | Operators can correlate a write attempt and its resulting receipt/verification | Include denials, uncertainty, and per-item batch results without private bodies or tokens |
| REQ-003 | Operators can see errors, timeouts, admission contention, read-budget exhaustion, and uncertain writes | Bounded labels; explain per-process versus deployment-wide scope |
| REQ-004 | Approved CI reproduces static/offline/package checks from locked dependencies | No inherited real keys or implicit live E2E/deployment |
| REQ-005 | Deployment/upgrade/rollback instructions preserve reader/writer isolation and accepted operation scope | No live configuration changed by writing the runbook |
| REQ-006 | Owned recovery rehearsal verifies data, permissions, history, and attachment checksums | Failed restore leaves applications stopped; no automatic reset fallback |

## 4. Public contract and technical specification

The following boundaries are fixed. Remaining implementation choices are explicit blockers,
not decisions an implementation agent may silently make.

| Area | Fixed boundary / outstanding specification |
|---|---|
| Existing health | Preserve unauthenticated `GET /health` with its current liveness response |
| Readiness | Separate local-runtime readiness and native availability; exact route/status/schema/probe policy decided under DEC-001 |
| Upstream checks | Bounded, side-effect-free; no issue/user data in health output; define authentication behavior without reusing a caller key across requests |
| MCP exposure | Health/metrics/audit are not registered as MCP tools; existing allowlist remains stable |
| Writer audit | Correlate request/operation, sanitized actor/target identifiers if approved, dispatch, outcome, verification, and batch-item result; field/retention/access contract under DEC-003 |
| Metrics | Low-cardinality operational counters/timings; no key, subject, arbitrary path, user ID, or target ID as a metric label; sink/export/access under DEC-003 |
| CI | Reuse Git Bash-compatible project commands; exact provider, triggers, Python version, artifact policy, and activation under DEC-002 |
| Packaging | Build and inspect wheel/sdist and non-root image; preserve locked dependencies and runtime import boundaries |
| Recovery | Separate stateless MCP configuration/image rollback from native DB/files recovery; exact ownership/objectives/procedure under DEC-004 |
| Compatibility | Existing tool names, schemas, auth, public limits, and liveness contract preserved |

Health and telemetry must not imply that every user can access every resource. A locally ready
application can still receive a caller-specific Redmine error. Readiness probes must not become
an unbounded workload or a mutation. Audit delivery failure must not cause an accepted write to
be retried or reclassified as rejected; define its operator signal before implementation.

CI must keep secrets/snapshots/generated state out of uploaded artifacts. Live E2E is never an
ordinary pull-request job. Registry publishing, workflow activation, public deployment, and
destructive rehearsal require explicit authorization in their execution assignments.

Specification exit: DEC-001..004 resolved and all endpoint/configuration/error/activation and
recovery contracts written. Until then, only decision resolution and specification are assignable.

## 5. Implementation plan

Execute these phases sequentially, each with an explicit scope and handoff.

| Phase | Work / ownership | Components | Gate |
|---|---|---|---|
| A | Resolve decisions; specify schemas, settings, trigger scope, retention, ownership, and objectives | This task and dashboard | Required before coding |
| B | Implement local readiness plus approved native-availability observation | `api/health.py`, lifecycle/runtime, Compose health guidance | Coding then separate authorized verification |
| C | Implement safe writer audit and bounded metrics | Existing API/service/gateway boundaries and observability | Coding then separate authorized verification |
| D | Add approved CI configuration and package/image checks | Selected provider files, existing Bash scripts, package/image definitions | Review files before platform activation |
| E | Write deployment/upgrade/rollback/recovery runbooks | `docs/operations.md`, configuration/testing guidance, new operational runbook if needed | Documentation before any rehearsal |
| F | Execute authorized operational and isolated recovery scenarios | Owned deployment and private fixtures/artifacts | No shared/external data replacement |
| G | Consolidate evidence and hand final release review to prep-009 | This task, current acceptance ledger, dashboard | No automatic publish/deploy |

Any dependency additions need explicit justification and matching `uv.lock`. Coding-only phases
do not create or execute tests. New operational docs belong to this task, not prep-021. Split a
phase into a new task only if the resolved contract introduces an independently owned prerequisite.

## 6. Acceptance criteria and traceability

| Criterion | Given / when | Then |
|---|---|---|
| AC-001 | Operator decisions are resolved | Exact implementation/activation contracts exist with no material uncertainty |
| AC-002 | Local startup/shutdown or Redmine outage is exercised | Liveness/readiness/native availability remain distinguishable without credentials/data leakage |
| AC-003 | Denied, accepted, uncertain, and batch writes occur | Safe audit reconstructs attempts/outcomes without changing mutation semantics |
| AC-004 | Capacity, timeout, and budget scenarios occur | Bounded metrics expose the cause and documented aggregation scope |
| AC-005 | Approved CI/build procedure runs | Locked quality/offline/package checks pass; no live calls or sensitive artifacts |
| AC-006 | Owned deployment is upgraded/rolled back | Reader/writer separation and accepted configuration scope remain intact |
| AC-007 | Owned restore succeeds or fails partway | Native data/files/permissions/history verified on success; failure stays stopped with a recovery path |

| Requirement | Criteria | Scenario | Result |
|---|---|---|---|
| REQ-001 | AC-001/002 | STAB-022-001/002 | Blocked by decisions; execution pending |
| REQ-002 | AC-003 | STAB-022-003 | Blocked by DEC-003 |
| REQ-003 | AC-004 | STAB-022-004 | Blocked by DEC-003 |
| REQ-004 | AC-005 | STAB-022-005 | Blocked by DEC-002 |
| REQ-005 | AC-006 | STAB-022-006 | Blocked by DEC-001 |
| REQ-006 | AC-007 | STAB-022-007 | Blocked by DEC-004 |

## 7. Test plan and execution record

| Scenario | Layer / procedure | Expected observation |
|---|---|---|
| STAB-022-001 | Manual specification review | Endpoints/settings/CI/retention/recovery objectives fully resolved |
| STAB-022-002 | Authorized offline lifecycle + owned outage | Readiness states correct during failed startup, running state, native outage, and shutdown; no secret output |
| STAB-022-003 | Authorized offline REST/MCP + batch | Attempt, denial, accepted/uncertain receipt, failed read-back, interrupted response, and audit-sink failure handled safely |
| STAB-022-004 | Authorized bounded contention/error scenarios | Metrics accurate, labels bounded, process scope documented, no behavioral regression |
| STAB-022-005 | Authorized CI/package/image checks | Clean locked environment, offline suite, isolated wheel imports, non-root image, redacted artifacts |
| STAB-022-006 | Authorized owned pilot rehearsal | Deploy/restart/upgrade/rollback reproducible; disabled operations remain denied |
| STAB-022-007 | Authorized separate disposable recovery environment | Fresh-volume restore matches IDs/history/permissions/files; incomplete/incompatible snapshots rejected; injected failure leaves service stopped |

Required live tooling and fixtures are specified only after environment decisions. Reuse
existing guards; never point destructive helpers at the shared E2E volumes or an external
instance merely to obtain recovery evidence. A reviewed runbook alone does not pass recovery.

| Evidence | Procedure | Actual result | Status |
|---|---|---|---|
| EVID-022-001 | Decision/specification review | Not performed | Blocked |
| EVID-022-002 | Assigned coding/static checks | Not run | Pending |
| EVID-022-003 | Explicitly authorized offline/CI/package verification | Not run | Pending |
| EVID-022-004 | Explicitly authorized pilot and owned recovery rehearsal | Not run | Pending |

## 8. Implementation and review record

- Changes made: planning document and dashboard only.
- No endpoint, logger, metrics exporter, workflow, dependency, deployment, or volume changed.
- No operational command or automated check executed.
- Open blockers are DEC-001..004; inherited implementation/acceptance tasks also remain prerequisites.
- Future evidence must distinguish local/runtime readiness, native service availability, functional
  acceptance, and recovery acceptance. None substitutes for another.

## 9. Completion and handoff

- [ ] Four operator decisions resolved; implementation contract reviewed.
- [ ] Readiness, writer audit, and metrics implemented with passing evidence.
- [ ] Approved CI/package procedure verified without implicit live calls or deployment.
- [ ] Deployment/rollback runbook and owned rehearsal verified.
- [ ] Recovery objectives and actual resulting data/files verified; failure path recorded.
- [ ] Current acceptance ledger, task/dashboard, and new operational guidance synchronized.
- [ ] Final release review handed to prep-009 without publishing or deploying automatically.

Final status: blocked. Next action: after the preceding tasks, resolve DEC-001..004 and complete
the exact operational specification before assigning phase B. This planning request authorizes
neither CI activation nor a destructive rehearsal or live deployment.
