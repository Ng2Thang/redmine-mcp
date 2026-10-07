# prep-003: Refactor the MCP runtime foundation

## 1. Task identity and status

| Field | Value |
|---|---|
| Task ID | prep-003-runtime-foundation |
| Assigned capability | Maintain consistent authentication, HTTP requests, exceptions, and logs across existing MCP readers |
| Type | Shared prerequisite |
| Access | Read-only |
| Destructive effects | None |
| Status | blocked |
| Dependencies | Existing runtime and prep-001 static checks; later authorized testing stage |
| Related tasks | Existing reader tasks; no new public operation |
| Target Redmine version | Redmine 7.0.2; runtime acceptance pending |
| Last updated | 2026-10-02, Codex |
| Progress summary | Implementation accepted with testing pending; prep-004 expanded offline verification (356-case suite passes) and verified the authorized MCP readiness fix. Static/build checks pass; full live matrix remains pending. |
| Next action | Review the authorized prep-004 offline evidence and complete the remaining synthetic identity/visibility/correlation matrix |

## 2. Discovery and evidence

The user requested repository structure for authentication, HTTP requests, exceptions, and
logging. Existing services already use Protocol ports, but identity lookup lived in FastAPI
dependencies, authorization accepted arbitrary `read:` names, transport configuration lived in
the app factory, and pagination checks differed across gateways. Existing staged changes were
preserved; this task adds unstaged changes without staging or committing them.

Evidence is the current source under `api/`, `common/`, `integrations/redmine/`, `mcp/`, and
`app.py`. N/A for new upstream endpoint evidence: this refactor introduces no Redmine endpoint
or query parameter. It establishes adapter validation rules; live compatibility is still pending.
Repository and user instructions require English Markdown, Git Bash commands, and no unit-test
execution without a separate user request. No testing skill or delegation was used.

Decisions: keep REST/MCP operation names and successful response shapes; use independent explicit
authorization and exposure lists; perform no automatic retries; generate correlation IDs on the
server; omit sensitive request/exception content from logs; keep identity request scoped.

## 3. Requirements

| ID | User need | Observable behavior |
|---|---|---|
| REQ-001 | Clear auth boundary | Framework-independent principal, identity Protocol, authentication service, and explicit read policy |
| REQ-002 | Isolated, bounded upstream transport | Per-request key, no shared cookies/default authorization, separate connect/pool timeouts and limits |
| REQ-003 | Consistent failures | Safe status mapping, sanitized unexpected errors, stream-aware failure behavior |
| REQ-004 | Useful safe logs | Server-generated request ID, operation/status/duration events, no secrets or caller/upstream content |
| REQ-005 | Reliable data conversion | Shared strict count/page/object validation and requested-resource ID checks |
| REQ-006 | Existing MCP readers keep working | Stable operation names, inputs, defaults, successful shapes, and per-user visibility |
| REQ-007 | Bounded upstream acquisition | Per-read deadline, streamed decoded-body limit, closure on success/failure, no error-body consumption |
| REQ-008 | Startup exposure guarantees | Normalized routes enforce read dependencies and response schemas; generated tool names match catalog |

## 4. Public contract and technical specification

The existing REST and MCP routes remain the interfaces. Authentication uses the personal
`X-Redmine-API-Key`; repeated, oversized, or malformed headers produce 401. Permission and MCP
exposure lists are explicit and separate. The new HTTP configuration is specified in
[configuration](../../configuration.md); defaults are forwarded by Compose and shown in `.env.example`.

Every HTTP response includes `X-Request-ID`. Internal ASGI requests inherit the current request
context. Application errors retain `error.code` and `error.message`. Unexpected errors before
response headers return sanitized `500 internal_error`; failures after headers terminate the
stream with sanitized exception text. Cancellation propagates.

Redmine 429 produces `502 upstream_rate_limited`; 503 produces `502 upstream_unavailable`;
504 and HTTP timeouts produce `504 upstream_timeout`. Pool acquisition timeout produces
`503 upstream_busy`. Other failures retain existing mapping. No retries or Retry-After
forwarding are provided. Upstream JSON and exception text are not returned or logged.

Counts must be nonnegative JSON integers. Page rows must be objects and cannot exceed the
requested limit. Supplied pagination echoes must match the requested integers; time entries
require echoes while issues/projects retain support for omitted echoes. Count/row consistency
is not inferred for paginated reads because results are not a snapshot. Complete unpaged
collections still require count equality. Detail IDs must match the requested resource.

Write semantics: N/A, read-only. No new write capability or administrative action.

Identity verification now receives the normalized key as a port argument, binding the verified
principal to the retained context key. Configurable per-read deadlines default to 60 seconds;
decoded-body limits default to 10 MiB. See configuration for scope and memory limitations. Payload
overflow maps to `502 upstream_response_too_large`. MCP validation normalizes version-dependent
FastAPI included routes and checks authorization dependencies, schemas, and generated tool names.

## 5. Implementation plan

| Step | Components | Result |
|---|---|---|
| 1 | `auth/`, `api/security.py`, bootstrap, Redmine identity adapter | Implemented |
| 2 | Redmine transport/client, settings, Compose, environment example | Implemented |
| 3 | Response envelopes, mapping, issue/project/time-entry gateways | Implemented |
| 4 | API middleware/error handlers, observability, app wiring | Implemented |
| 5 | Architecture/configuration/tool/development docs and changelog | Updated |
| 6 | Static checks and credential-free startup smoke | Passed |
| 7 | Offline scenarios and marked synthetic Inspector checks | Deferred to separately authorized testing |
| 8 | Strict query contracts, service validation, dedicated lifecycle, MCP hints, import-boundary/cycle gate | Implemented after comparing the user-provided layout |

No dependencies or lockfile changes.

## 6. Acceptance criteria and traceability

| Criterion | Requirement | Required evidence | Status |
|---|---|---|---|
| AC-001 | REQ-001 | Header rejection, current-user identity, allow/deny policy scenarios | Pending; missing-key smoke passes |
| AC-002 | REQ-002 | Concurrent identities, cookie exclusion, limits, redirect and timeout scenarios | Pending |
| AC-003 | REQ-003 | Status mapping and unexpected/stream/cancellation scenarios | Pending |
| AC-004 | REQ-004 | Request/header/log correlation, context cleanup, secret exclusion | Pending; health/401 correlation smoke passes |
| AC-005 | REQ-005 | Strict envelopes, resource mismatch, complete collections | Pending |
| AC-006 | REQ-006 | REST/MCP discovery and authorized invocation with synthetic accounts | Pending |
| AC-007 | REQ-007 | Streaming limit, deadline, cancellation, and closure scenarios | Pending |
| AC-008 | REQ-008 | Missing dependency/schema, duplicate/hidden route, generated-catalog mismatch | Pending; valid catalog startup passes |

## 7. Test plan and execution record

These scenarios are a handoff, not permission to run tests in this assignment. A future testing
assignment can use existing pytest/pytest-asyncio dependencies, HTTPX MockTransport, fake settings
without `.env`, explicit ASGI lifespan, and MCP SDK sessions. Use only synthetic fixture keys.

| Scenario | Coverage | Expected result |
|---|---|---|
| FOUNDATION-001 | Missing/repeated/blank/control/non-ASCII/oversized keys; identity 401/403/malformed user; allow/deny policy | Safe auth errors, correct identity, no forbidden dispatch |
| FOUNDATION-002 | Two concurrent personal keys; upstream Set-Cookie; default auth; relative paths; redirects | Each call uses its own key; no outgoing cookie/default auth; redirects not followed |
| FOUNDATION-003 | Pool/connect/read timeouts; transport errors; 429/503/504; invalid JSON | Documented safe statuses/codes, no retry or leaked upstream content |
| FOUNDATION-004 | Application failure; unexpected failure; failure after streaming starts; cancellation | Sanitized responses/stream exceptions; cancellation propagates |
| FOUNDATION-005 | Concurrent REST/MCP/internal calls; malicious incoming request ID; log capture | Context isolation and inheritance, safe logs, header correlation, context reset |
| FOUNDATION-006 | String/boolean/negative counts; non-object rows; oversized pages; missing/mismatched echoes; empty/short pages; wrong detail ID | Strict rejections, valid pages and omission metadata preserved |
| FOUNDATION-007 | All catalog operations and authorized synthetic accounts through Inspector; lifespan shutdown | Stable tools, correct per-user visibility, clients/transports close |
| FOUNDATION-008 | Direct service calls with boolean/negative IDs, bad pagination, invalid status/sort, naive datetime, missing project, invalid/duplicate includes | Sanitized input error before gateway dispatch; valid requests keep the same mapping |
| FOUNDATION-009 | Partial startup, one cleanup failure, closed runtime client, repeated lifespan, MCP discovery annotations | Remaining resources close, safe runtime errors, explicit lifespan ownership, correct client hints |
| FOUNDATION-010 | Concurrent authentication with distinct keys; normalized key passed to identity port | Principal and retained key correspond to the same verification request |
| FOUNDATION-011 | Slow streamed body; timeout/cancellation; payload exactly at limit/over limit; malformed/deep JSON; large error body | Safe deadline/size/data errors; streams close; error status maps before reading body |
| FOUNDATION-012 | Lazy/flat route representations; hidden/duplicate routes; missing read dependency/schema; generated tool mismatch | Valid protected tools start; invalid exposure fails startup |

| Evidence | Procedure | Actual result | Date |
|---|---|---|---|
| EVID-001 | `bash scripts/doctor.sh` | Prerequisites ready; Git Bash, Python 3.13.3, uv available | 2026-10-01 |
| EVID-002 | `bash scripts/check.sh` | Ruff lint/format pass; strict mypy passes for 52 source files | 2026-10-01 |
| EVID-003 | `uv run --frozen uvicorn redmine_mcp.app:create_app --factory --host 127.0.0.1 --port 18080 --no-access-log` | Startup completed on a temporary localhost port; process stopped after smoke checks | 2026-10-01 |
| EVID-004 | `curl --include http://127.0.0.1:18080/health` and an unauthenticated `GET /api/v1/projects` | 200 health, 401 missing key; distinct request IDs match timing logs | 2026-10-01 |
| EVID-005 | Final `bash scripts/check.sh` | Ruff lint/format and strict mypy pass; AST architecture boundaries and cycles pass for 61 runtime modules | 2026-10-01 |
| EVID-006 | Temporary localhost Uvicorn on port 18080; health, missing-key request, then Ctrl+C | Application startup and shutdown complete; 200/401 responses have request IDs matching logs | 2026-10-01 |
| EVID-007 | Final static checks after bounded HTTP and route-contract changes | Ruff/format, mypy, and architecture checks pass for 63 runtime modules | 2026-10-01 |
| EVID-008 | Startup with stronger MCP exposure checks, health/missing-key requests, Ctrl+C | Initially exposed lazy-router compatibility issue; corrected adapter then completed startup/shutdown and 200/401 correlation smoke | 2026-10-01 |
| EVID-009 | Authorized prep-004 Inspector 2.8.0 sample against marked Previously inspected Redmine, local app port 18080, restricted reader key | Eleven catalog operations discovered; ten sample calls succeeded. Category lookup returned 403 for reader, consistent with pinned `manage_categories` permission; admin sample succeeded. This partially covers FOUNDATION-007, but concurrent identities, full visibility matrix, and other foundation scenarios remain pending. | 2026-10-01 |
| EVID-010 | Authorized prep-004 offline continuation and user-approved MCP startup fix | Expanded full suite: 356 passes; static checks and source/wheel build pass. Foundation coverage, deterministic manager readiness, concurrent caller isolation, failed/cancelled startup, and open-session shutdown are recorded in the dated verification ledger. | 2026-10-02 |

The earlier coding stage ran no unit tests, mock execution, authenticated tool calls, or
Inspector checks. EVID-009 records a later authorized partial Inspector check. The normal
startup/shutdown smoke and that sample do not prove streaming failures, partial-startup cleanup,
or shutdown behavior with active MCP sessions.

## 8. Implementation and review record

The module boundaries and contracts are documented in [architecture](../../architecture.md).
Package public interfaces are declared with `__all__` across runtime and administrative packages.
External imports use package interfaces; implementation imports within each package remain direct.
An import-only smoke loaded every declared public symbol in all 14 packages without network or
seed execution. Static checks pass, including re-export-aware boundary and cycle validation.
HTTP statuses now use FastAPI's named constants throughout runtime code and existing test
assertions. Only the constants namespace is exempted from the framework import restriction.
Ruff, formatting, mypy, architecture checks, and whitespace checks pass after this mechanical
refactor; no unit tests were executed. Status values and response contracts remain the same.
The user-provided layout was evaluated by responsibility: dedicated auth and lifecycle modules,
MCP client hints, and query/business validation were implemented. Existing `features/` grouping
retains services and ports. OAuth, extension APIs, upload/download managers, background offload,
and MCP Apps require actual capability contracts. The architecture document records this mapping.
Static checks initially found an import-order issue and an old `AuthContext` import; both were
fixed. Existing staged work remains intact. Authentication caches, generic connector frameworks,
distributed tracing, automatic retries, and additional endpoints are outside this assignment.

## 9. Completion and handoff

- [x] Required code and documentation implemented.
- [x] Repository static checks pass.
- [x] Credential-free startup and missing-key smoke recorded.
- [ ] Every requirement has runtime acceptance evidence.
- [ ] Separately authorized offline scenarios pass.
- [ ] Synthetic Inspector acceptance passes.

Final status: **blocked - implementation accepted with testing pending; offline verification expanded, live matrix pending**.

On 2026-10-02 the user accepted the implementation with testing pending and requested prep-004.
The user also authorized the runtime fix after testing exposed the MCP startup race.
See [prep-004 verification](../../testing/evidence/prep-004-verification.md) for executed foundation cases and
remaining variants. Full runtime acceptance, including a second ordinary synthetic identity
and the live permission/correlation matrix, remains pending.
