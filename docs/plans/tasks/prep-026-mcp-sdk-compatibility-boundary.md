# prep-026-mcp-sdk-compatibility-boundary: Isolate private SDK integration

## 1. Task identity and status

| Field | Value |
|---|---|
| Task ID | prep-026-mcp-sdk-compatibility-boundary |
| Assigned capability | Keep tool dispatch, discovery and session lifecycle stable when maintaining the pinned MCP adapter |
| Type / access | Shared internal refactor; existing reader and restricted writer catalog |
| Destructive effects | None introduced; existing authorized writer invocations retain their effects |
| Status | planned |
| Dependencies | [prep-022](prep-022-mcp-schema-parity.md) accepted; existing session/discovery/receipt contracts and [prep-020](prep-020-current-catalog-acceptance.md) baseline |
| Related tasks | prep-010..015 implementations, prep-019, prep-023/025/026; [dashboard](../index.md) |
| Target Redmine version | 7.0.2; adapter refactor unverified |
| Last updated | 2026-10-07, Codex |
| Progress summary | Compatibility boundary and behavior invariants specified; no refactor |
| Next action | Accept prep-022, then review/assign this refactor and its separate verification stage |

## 2. Discovery and evidence

Private SDK integration is spread across `registration.py`, `read_limits.py`, `discovery.py`
and `membership_transport.py`. It includes FastAPI-MCP `_request`, `_http_transport`, transport
manager/task/start flags and SDK `_tool_cache`. Several hooks are necessary for pinned-version
session startup, immutable discovery schemas, logical budgets and membership DELETE bodies.
This is a maintenance risk rather than evidence of a current runtime failure.

| Source | Inspected | Evidence / limitation |
|---|---|---|
| `mcp/registration.py` | 2026-10-07 | Manual manager startup, readiness future, shutdown and private transport fields |
| `mcp/discovery.py`, `read_limits.py` | 2026-10-07 | Request handler wrappers, direct SDK cache access and request-context assumptions |
| `mcp/membership_transport.py` | 2026-10-07 | FastAPI-MCP `_request` replacement for membership DELETE JSON |
| `lifecycle.py`, `app.py`, `api/security.py` | 2026-10-07 | Lifespan cleanup order, original request authentication and session owner identity |
| Installed FastAPI-MCP 0.4.0 and MCP SDK 1.30.0 source; `pyproject.toml`, `uv.lock` | 2026-10-07 | Existing versions are pinned; private behavior is not a cross-version public guarantee |
| [MCP tools specification](https://modelcontextprotocol.io/specification/2025-11-25/server/tools) | 2026-10-07 | Public tool schemas/results; does not guarantee Python private attributes |
| `deploy/compose.test.yaml`, [ledger](../current-catalog-acceptance.md) | 2026-10-07 | Existing target/functional baseline; no new Redmine API claim |

Baseline: clean `36ff5f0` before planning. Follow repository architecture, Git Bash/English and
explicit test authorization. No new analysis artifact is needed: this conversation and source
inspection establish the refactor's outcome and boundaries.

| Decision | Resolution | Blocking? |
|---|---|---|
| DEC-001 | Keep FastAPI-MCP 0.4.0 and MCP 1.30.0; no upgrade or replacement MCP framework | No |
| DEC-002 | One typed compatibility module owns third-party private access and handler installation | No |
| DEC-003 | Preserve public registration/lifecycle entry points and all tool behavior | No |
| DEC-004 | Use sanitized startup compatibility failures; no fallback that disables auth, validation, budgets or DELETE bodies | No |

## 3. Requirements

| ID | Required observable behavior | Constraint |
|---|---|---|
| REQ-001 | Vendor private access is isolated behind a typed adapter boundary | Runtime modules outside that boundary do not read/write the identified private attributes |
| REQ-002 | Supported package versions and required hook shapes are checked before serving | Exact existing pins; no installation/upgrade by the application |
| REQ-003 | Repaired schemas, immutable deployment cache and caller-specific discovery survive the refactor | prep-022 acceptance precedes refactor acceptance |
| REQ-004 | DELETE body handling, sanitized errors, read budgets and writer receipt behavior remain equivalent | REST remains the authorization and execution boundary |
| REQ-005 | Startup/shutdown/cancellation preserve readiness and resource cleanup | No hanging future, orphan manager task, credential leak or cross-caller session |

Out of scope: new tools, schema/unknown-input policy changes, response field preservation,
dependency upgrades, native permissions, generic plugin framework, HTTPX proxy-parser refactor,
production deployment and new observability features.

## 4. Public contract and technical specification

| Area | Decision |
|---|---|
| Operations / routes / inputs | Existing catalog and all current `/api/v1/` and `/mcp` behavior |
| Schemas / outputs | Accepted prep-022 repair; existing result content, envelopes and annotations |
| Auth | Existing native caller key, admitted writer, operation ceiling and SDK owner binding |
| Native calls | Existing same-key REST/gateway path; no direct database or native endpoint addition |
| Configuration | No new setting; existing pinned package versions are supported |

Create `mcp/compatibility.py` with a typed `MCPCompatibility` facade. It owns:

1. Version/shape checks for the pinned FastAPI-MCP and SDK; required server handlers/tool cache,
   internal request callable, transport fields and manager lifecycle must exist in their expected
   forms. Validate registration-stage shapes before installing hooks and transport-stage shapes
   after mounting but before publishing ready startup.
2. Access/replacement of the original REST request hook and the exact membership DELETE-body
   override, without introducing generic request rewriting.
3. Snapshotting/seeding of the full repaired tool schema cache and installation/wrapping of
   ListToolsRequest/CallToolRequest handlers. Discovery and budget policy remain in their current
   modules; they receive typed facade methods instead of vendor-private objects.
4. Native request-context extraction for discovery, retaining the authenticated original request
   and existing session/caller isolation.
5. Transport manager creation, start flags/task/future coordination and shutdown access. Lifecycle
   entry points remain stable wrappers; resource ownership stays per application lifespan.

Keep `register_mcp`, `start_mcp` and `shutdown_mcp` public behavior and the existing `app.state.mcp`
object available to current callers/tests. Facade helper construction may use the existing object;
do not introduce a process-global cache. Failures do not expose exception strings, package paths,
keys or request content. Existing safe startup code/message is retained.

Registration order is explicit: select/validate catalog, install request-body compatibility,
repair schema, annotate, seed immutable schema superset, install caller discovery and budget
wrappers in the accepted order, mount, validate/start the manager, then publish readiness.
Do not overwrite an earlier wrapper or let lazy SDK discovery create a second budget inside a
tool invocation. If hook ordering differs from current implementation, prove equivalent behavior
in named scenarios rather than assuming handler replacement is harmless.

| Scenario | Public behavior |
|---|---|
| Unsupported version or missing/incompatible hook | Sanitized startup failure; no partially usable tool server |
| Invalid input/auth/permission/read budget | Existing safe REST/MCP result; validation/auth/budget not bypassed |
| Accepted or uncertain writer call | Existing receipt/read-back/reconciliation semantics |
| Failed manager startup | Startup future resolves with safe failure; owned tasks/resources cleaned |
| Cancellation/shutdown | Cancellation propagates; owned manager and clients closed in existing order |

Writes retain their single-dispatch, no-retry, no-rollback contract. No mutations occur during
planning. Authorized live acceptance uses existing owned fixtures and only task-owned cleanup.
Pagination, model validation and attachment links are unchanged. Specification exit: boundary,
supported versions, hook order and compatibility invariants are fixed.

## 5. Implementation plan

| Step | Concrete change | Files/components |
|---|---|---|
| 1 | Inventory private accesses and implement typed version/shape facade | New `mcp/compatibility.py`; no installed-package edits |
| 2 | Replace direct cache/request-context/request-handler access | `mcp/discovery.py`, `mcp/read_limits.py`, `membership_transport.py` |
| 3 | Delegate transport start/shutdown and preserve readiness/cleanup | `mcp/registration.py`, `lifecycle.py` only as needed |
| 4 | Keep schema repair and tool/auth policy outside compatibility internals | Accepted prep-022 module; annotations/catalog/security |
| 5 | Document pins, upgrade procedure and named compatibility invariants | Architecture/development/changelog/task/dashboard |
| 6 | Hand off SDK, lifecycle/failure-injection and owned Inspector scenarios | Separate verification assignment |

No dependency/lockfile change. Preserve work from prep-023/025/026 when present; preferred sequence
places this refactor last, though only prep-022 is a new hard dependency. Do not revert others'
edits or merge their behavior changes into this refactor's ownership.

## 6. Acceptance criteria and traceability

| Criterion | Given / when | Then |
|---|---|---|
| AC-001 | Runtime source and facade are inspected | Identified private accesses exist only in compatibility module; policies use typed methods |
| AC-002 | Versions/hooks are correct or incompatible | Correct pins start; incompatibility fails before ready with safe errors |
| AC-003 | Two callers discover/invoke tools | Repaired immutable schemas and caller/session isolation remain |
| AC-004 | Membership DELETE, budget failure and writer uncertainty occur | Existing payload/receipt/error behavior remains; one mutation at most |
| AC-005 | Startup or shutdown is interrupted/fails | Future/task/client cleanup completes without hang or sensitive exception text |

| Requirement | Criterion | Scenario | Evidence / result |
|---|---|---|---|
| REQ-001 | AC-001 | SDK-026-001 | Pending; not run |
| REQ-002 | AC-002 | SDK-026-002 | Pending; not run |
| REQ-003 | AC-003 | SDK-026-003/006 | Pending; not run |
| REQ-004 | AC-004 | SDK-026-004/006 | Pending; not run |
| REQ-005 | AC-005 | SDK-026-005/006 | Pending; not run |

## 7. Test plan and execution record

Test implementation/execution, startup, Inspector and synthetic mutations require a separate
assignment. Catalog counts alone are not behavioral acceptance.

| Scenario | Layer / setup | Observable assertion |
|---|---|---|
| SDK-026-001 | Authorized source/architecture review | No identified private access outside facade; typed policy/lifecycle ownership retained |
| SDK-026-002 | Offline metadata/shape fault injection | Unsupported versions, absent/wrong cache/handler/request/transport hooks fail safely before ready |
| SDK-026-003 | Offline actual pinned SDK with two keys | Null/union invocation from prep-022, immutable cache, discovery/admission and session reuse rejection |
| SDK-026-004 | Offline actual SDK/ASGI/MockTransport | Membership DELETE carries JSON; read budgets remain fresh; writer 500/timeout receipts and safe errors unchanged |
| SDK-026-005 | Offline manager/client failure and cancellation injection | Startup future completes; owned task/client cleanup and readiness ordering do not hang |
| SDK-026-006 | Authorized owned 7.0.2 and Inspector | Startup/list/call/shutdown, reader/writer gates, selected membership lifecycle and owned cleanup |

Future Git Bash procedures: `bash scripts/check.sh`, assigned session/runtime/bounded-read and
membership/schema integration scenarios, then owned startup/Inspector. Use current installed
versions and mocked metadata for incompatibility cases; do not install alternative dependencies
to run tests. A package build is needed only if package layout/dependency metadata changes.

| Evidence | Procedure | Actual result | Status |
|---|---|---|---|
| EVID-026-001 | Source and installed-dependency inspection on 2026-10-07 | Private integration locations identified; no runtime regression run | Planning only |
| EVID-026-002 | Static/offline/lifecycle/native/Inspector scenarios | Not run | Pending |

## 8. Implementation and review record

Only task/dashboard documents created. Facade implementation, hook-order review, private-access
inspection, static checks and all SDK/live cases are pending. Existing pinned-version acceptance
does not imply this future refactor passes. No upgrade or unrelated behavior change is authorized.

## 9. Completion and handoff

- [ ] Typed facade owns private SDK integration.
- [ ] Version/shape, hook order and schema/session invariants accepted.
- [ ] Lifecycle failure/cancellation and receipt/error cases pass.
- [ ] Required owned Inspector/native cleanup evidence recorded.
- [ ] Documentation/final diff/task/dashboard synchronized.

Final status: planned. Contract blockers: none; prep-022 acceptance is an implementation
dependency. Next action: finish and accept prep-022, review this refactor, then assign coding and
SDK-026-001..006 verification separately.
