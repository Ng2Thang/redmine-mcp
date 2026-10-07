# PREP-027: Bounded retries for Redmine reads

## 1. Task identity and status

| Field | Value |
|---|---|
| Task ID | prep-027-redmine-read-retries |
| Assigned capability | Existing REST/MCP callers recover from transient Redmine read failures within existing resource limits |
| Type | Shared prerequisite extending existing upstream GET behavior; no new tool |
| Access | Read requests, including identity, discovery, authorization, writer preflight and read-back GETs |
| Destructive effects | None; mutations remain single attempt |
| Status | complete |
| Dependencies | Existing prep-015 budgets, prep-019 write receipts, prep-020 catalog baseline, prep-023 membership batch budgets; prep-016/017/018 testing infrastructure for separately authorized verification |
| Related tasks | [prep-015](prep-015-bounded-redmine-reads.md), [prep-019](prep-019-write-outcome-consistency.md), [prep-023](prep-023-membership-batch-budgets.md), [bug-001](../bugs/bug-001-get-issue-upstream-response.md) |
| Target Redmine version | Redmine 7.0.2; selected owned reader compatibility accepted |
| Last updated | 2026-10-07, Codex |
| Progress summary | 103 focused cases, 92 corrected legacy contract cases and 2 owned live reader cases pass; full regression run has 1,457 passes and 41 old assertions, all resolved in final targeted reruns; startup/Inspector/static/architecture pass |
| Next action | None for PREP-027; Bug-001 still requires its original sanitized malformed payload |

## 2. Discovery and evidence

### Client outcome and repository baseline

- A caller should receive a successful issue or project read when a temporary connection failure
  or unavailable upstream recovers promptly, without manually repeating the whole tool.
- Existing tools already serve the requested outcomes. This task changes their shared GET client
  rather than adding MCP operations, inputs, or routes.
- `integrations/redmine/client.py::RedmineClient.get` makes one streamed GET under a per-read
  deadline, closes responses, bounds decoded bytes, then parses JSON and maps attachment links.
  `get_page` uses that method for pagination probes and requested pages.
- `integrations/redmine/transport.py` explicitly sets HTTPX `retries=0`. Its admitted transport
  charges each physical request and holds a shared semaphore permit until response closure.
- `common/read_budget.py` supplies aggregate request, byte and time limits. Reader defaults are
  30 requests, 10 MiB and 90 seconds; membership batches use their own configured limits.
- `integrations/redmine/identity.py` uses `RedmineClient.get` for `users/current.json`.
  `bootstrap.py::read_policy` supplies the same read policy to identity and feature clients.
- Example flow: `features/issues/router.py` -> `IssueService` -> `IssueReader` ->
  `integrations/redmine/issues.py` -> `RedmineClient.get("issues/{id}.json", params)`.
  MCP registration reuses these REST operations through `mcp/registration.py`.
- `integrations/redmine/write.py::RedmineWriter` makes single-attempt JSON and binary mutations.
  Received 5xx and dispatched transport failures can return uncertain receipts. GET preflight
  and read-back failures must preserve those existing receipt semantics.
- Follow-up HTTP audit: upstream dispatch sites in runtime source are `RedmineClient.get`
  and `RedmineWriter._write`; feature gateways use the shared reader. Internal MCP dispatch
  uses `MCPRestClient` and `MCPCompatibility`, not a second network call to Redmine.
- `app.py` uses an in-process HTTPX ASGI transport for MCP-to-REST calls. Inspection of the
  installed `.venv/Lib/site-packages/httpx/_transports/asgi.py` shows it awaits the ASGI app
  without enforcing the request timeout extension. The configured internal HTTPX timeout
  must not be treated as an enforced whole-tool timer or as a reason to replay a request.
- `CapabilityService.authorize/candidates` and `ProjectCapabilityService.list_capabilities`
  have existing enclosing async timeouts. `ProjectMembershipService.manage` deliberately uses
  a cooperative batch budget without cancelling the entire batch, preserving write receipts.
  Read retry must respect both forms of deadline without introducing whole-writer cancellation.
- Instructions: repository `AGENTS.md`, `CONTRIBUTING.md`,
  [tool workflow](../../workflows/redmine-tools.md), and the planning/analysis skills.
  English Markdown, Git Bash, router -> service -> port -> gateway, no verification without
  a separate assignment. The original request authorized planning documents only. The user
  subsequently assigned implementation and review fixes, then explicitly approved Ruff,
  formatting and mypy static checks. The user subsequently assigned testing on 2026-10-07.
- Working tree before this plan: existing edits to `docs/plans/index.md` and untracked
  `docs/plans/bugs/`. Preserve those records and all unrelated changes.
- Runtime uses each caller's key; a credential-free shared pool provides capacity. Readers stay
  read-only; writers retain existing opt-in deployment, operation gates and native permissions.

### Upstream evidence

| Source URL or versioned source | Date inspected | Version supported | Endpoint/behavior | Permission required | Evidence or limitation |
|---|---|---|---|---|---|
| [HTTPX transports](https://www.python-httpx.org/advanced/transports/) | 2026-10-07 | Documentation; confirm locked package during implementation | Built-in retry covers connection errors/timeouts, not status retries | N/A | Retain `retries=0`; application loop must preserve physical-attempt accounting |
| [RFC 9110, section 9.2.2](https://www.rfc-editor.org/rfc/rfc9110.html#section-9.2.2) | 2026-10-07 | HTTP semantics, independent of Redmine release | Repeating requests and idempotency | Existing endpoint authorization | Supports a GET-only boundary; this task grants no mutation retry guarantee |
| [RFC 9110, section 10.2.3](https://www.rfc-editor.org/rfc/rfc9110.html#section-10.2.3) | 2026-10-07 | HTTP semantics | `Retry-After` as delay-seconds or HTTP-date | N/A | Header is advisory upstream evidence, not proof that a subsequent request succeeds |
| [Redmine REST API](https://www.redmine.org/projects/redmine/wiki/Rest_api) | 2026-10-07 | Current documentation; not version-specific acceptance | Per-request `X-Redmine-API-Key` authentication | Current caller key and endpoint permission | Retry must retain the requesting user's identity; no permission expansion |
| `deploy/compose.test.yaml`, existing accepted prep-020/023 records | 2026-10-07 | Pinned Redmine 7.0.2 | Existing GET endpoints and reader/writer boundaries | Existing contracts | New retry acceptance is pending; no new endpoint or version-specific capability is assumed |

Attempts to read upstream 7.0.2 controller source through web tools were unavailable during
planning. This policy does not depend on a new controller feature or assume native idempotency
keys. Synthetic 7.0.2 compatibility remains required acceptance evidence.

Differences from the public baseline: eligible GETs may take multiple physical attempts within
one unchanged deadline. Successful models and final error mappings remain compatible. Pagination,
visibility and malformed-data rules retain their existing owners.

| Client outcome / tool | Existing coverage | Read/write | Version support | Task ID | Dependencies | In scope/deferred |
|---|---|---|---|---|---|---|
| Recover an existing Redmine GET after a transient failure | All calls through `RedmineClient.get`, including `get_issue` | Read | Existing 7.0.2 baseline; new acceptance pending | prep-027 | Existing budgets and catalog baseline | In scope |
| Automatically repeat an upstream mutation | `RedmineWriter` and writer receipts | Write | No retry guarantee assumed | N/A | Separate future contract required | Deferred |
| Resolve `Unexpected Redmine data` | bug-001 | Read | Failing response remains unavailable | bug-001 | Sanitized failing evidence | Separate investigation |

### Questions and decisions

| ID | Question/assumption | Evidence or decision | Blocking? | Resolution date |
|---|---|---|---|---|
| DEC-001 | Where should retry live? | `RedmineClient.get`, before public error conversion; no retry loop in tools, services, or shared low-level transport | No | 2026-10-07 |
| DEC-002 | How many attempts by default? | Three total attempts, including the first; operator can set one to disable | No | 2026-10-07 |
| DEC-003 | Which failures qualify? | Exact transport classes and status allowlist in section 4; malformed data and local saturation are excluded | No | 2026-10-07 |
| DEC-004 | What about writes? | GET preflight/read-back can retry; POST/PUT/PATCH/DELETE and uploads remain single attempt | No | 2026-10-07 |
| DEC-005 | Does this fix bug-001? | No such claim: its validation boundary remains unknown; application `upstream_response` is excluded from retry | No | 2026-10-07 |
| DEC-006 | Does another HTTP layer need a retry loop? | No additional runtime dispatch path requires one; central GET retry covers upstream reads. Internal REST, middleware, MCP session and transport layers remain single dispatch | No | 2026-10-07 |
| DEC-007 | How does cooperative batch timing constrain GET backoff? | Clip each GET acquisition and its waits to the batch's remaining time; report its existing deadline error while retaining prior mutation receipts | No | 2026-10-07 |

## 3. Requirements

### Goal and boundaries

- Intended user: existing REST/MCP callers affected by short-lived Redmine read failures.
- In scope: bounded GET retry, configuration, cancellable backoff, safe logs, resource accounting,
  existing read/error compatibility, and documentation of the new timing behavior.
- Out of scope: mutation replay, whole-tool or batch replay, malformed-data repair, persistent
  rate-limit queues, circuit breakers, redirects, new MCP inputs, tools, or database access.
- Future enhancements: any broader status policy or mutation retry requires its own evidence
  and contract review.
- Compatibility: existing operation IDs, request parameters, schemas, authorization and receipt
  semantics; earlier physical-attempt and byte expenditure is never discarded.
- Prerequisites: current Redmine configuration and caller permissions; no new privileges.

| ID | User need and intended outcome | Required observable behavior | Prerequisites/constraints |
|---|---|---|---|
| REQ-001 | Recover temporary read failures | Retry only eligible GET transport failures/statuses, up to the configured total attempts | Same path, params and caller key on every attempt |
| REQ-002 | Avoid repeated persistent failures or mutations | Noneligible errors fail immediately; mutations dispatch once | Preserve malformed-data rejection and writer receipts |
| REQ-003 | Bound load and waiting | Backoff, header delay, attempt cap, unchanged total deadline and aggregate budget | Close response and release capacity before waiting |
| REQ-004 | Tune recovery without changing tools | Validated environment settings with three attempts by default and one disabling retries | No client-side retry input |
| REQ-005 | Preserve trustworthy results and diagnostics | Existing output/final error mapping, credential isolation, safe retry logs and cancellation | No upstream body, key, URL/query or exception text in logs |
| REQ-006 | Avoid retries multiplying across HTTP layers or outliving parent work | One retry owner; respect enclosing capability/reader deadlines and cooperative batch remaining time | No whole-tool, internal REST, session or mutation replay |

Synthetic examples: GET `issues/101.json` returning 503 then a valid 200 yields the usual
`IssueDetail` after two attempts. A 200 with an invalid declared field yields the existing
`upstream_response` after one GET. A mutation returning 503 produces its existing uncertain
receipt after one mutation, even when configured GET attempts are three.

## 4. Public contract and technical specification

### Tool and REST interface

| Area | Decision |
|---|---|
| Existing or new tool | Shared behavior for existing tools; no new tool |
| Stable operation ID | Preserve every current ID, including `get_issue` |
| Purpose and tool description | Existing descriptions retained; document recovery policy in shared guides |
| REST method and route | Existing reader routes; for example `GET /api/v1/issues/{issue_id}` |
| Authentication and authorization | Repeat only the same caller's authorized GET; never switch keys or cache stale permission decisions |
| MCP exposure | Existing explicit allowlist and annotations; no registration changes |

### Inputs

| Field/location | Type | Required/default | Validation | Omitted/null/empty behavior | Upstream mapping |
|---|---|---|---|---|---|
| `REDMINE_READ_RETRY_MAX_ATTEMPTS` / Settings | Integer | Default `3` | `1..5`, inclusive | Omitted uses default; invalid values fail startup | Total GET attempts; `1` disables retries |
| `REDMINE_READ_RETRY_BASE_DELAY_SECONDS` / Settings | Float | Default `0.5` | Positive finite | Omitted uses default; invalid values fail startup | Exponential backoff base |
| `REDMINE_READ_RETRY_MAX_DELAY_SECONDS` / Settings | Float | Default `5` | Positive finite and at least base delay | Omitted uses default; invalid values fail startup | Maximum scheduled delay; excessive header delay prevents retry |
| Existing tool inputs | Existing types | Existing defaults | Existing validators | Existing semantics | Same encoded query/path on each attempt |

Use matching `redmine_read_retry_*` fields in `Settings` and `retry_*` fields in `ReadPolicy`.
`bootstrap.read_policy` forwards them to all `RedmineClient` instances. Keep defaults aligned.
The writer may receive that same policy object but must ignore retry fields.

### Outputs and mapping

- Preserve response models, optional fields, visibility observations and successful REST/MCP
  results. No attempt count or new envelope is added to public outputs.
- Preserve pagination depth, ordering and expansions. Retry only the failing GET, not successful
  probe requests, earlier pages, mutations, or the whole service operation.
- Preserve per-attempt `X-Redmine-API-Key`, relative-path validation, cookie/authorization removal,
  shared credential-free pools, disabled redirects and existing upstream success status checks.
- Request example: `{"issue_id":101,"include":"journals,attachments"}` through MCP. A retry
  returns the same existing issue model; exhausted retries return, for example,
  `{"error":{"code":"upstream_unavailable","message":"Redmine is unavailable"}}` using
  the actual existing message constant rather than introducing new wording.

### Exact eligibility and backoff

1. Retry GET failures of these HTTPX classes: `ConnectError`, `ConnectTimeout`, `ReadError`,
   `ReadTimeout`, `WriteError`, `WriteTimeout`, and `RemoteProtocolError`. They qualify before
   headers or during streamed body acquisition; discard any partial buffer before the next
   attempt. Previously charged decoded bytes remain charged.
2. Retry upstream HTTP `429`, `502`, `503`, and `504`. HTTP 500 and all other statuses are
   excluded from this initial conservative allowlist. Inspect upstream status before mapping
   to `ApplicationError`; do not classify by the application's outgoing REST status.
3. Exclude `PoolTimeout`, semaphore admission failures, all budget/deadline errors, cancellation,
   invalid paths, 3xx, 400/401/403/404/422, oversized responses, invalid JSON, resource/model
   validation failures, invalid attachment links, decoding failures and other exception classes.
   A response cleanup failure is not a retry signal.
4. For retry number `r` starting at one, compute `b = min(max_delay, base_delay * 2**(r-1))`.
   Choose jittered backoff uniformly in `[b/2, b]`. Defaults give waits of 0.25..0.5 seconds and
   0.5..1 second when no header delay applies. Inject clock, randomness and sleep into helpers
   for later deterministic tests; production waiting is asynchronous and cancellable.
5. On eligible HTTP statuses, parse a single `Retry-After` header as nonnegative integer seconds
   or HTTP-date. Convert dates to nonnegative seconds using UTC wall time. Missing, invalid,
   conflicting or multiple values use backoff. Never log header contents. A valid delay sets
   `wait = max(backoff, header_delay)`. If header delay exceeds `max_delay`, stop and return the
   current mapped error; do not retry earlier than requested.
6. Close the previous response in `finally` before sleeping or dispatching again. Error bodies
   are never consumed for retry decisions. Release the admitted transport permit during backoff.
   Build a fresh GET request and response buffer on every attempt; preserve the same parameters.
7. Start one absolute monotonic deadline for the complete GET acquisition, including all attempts,
   admission waits, cleanup and backoff. Do not reset `REDMINE_REQUEST_DEADLINE_SECONDS` each
   attempt. An enclosing reader/capability timer can end sooner. A membership batch instead has
   a cooperative deadline: compute its remaining time from the current budget and clip this GET
   acquisition timer to that remaining time. Apply this clipping only to GETs, not mutations or
   the complete writer/batch operation. On timer expiry, check the current aggregate deadline
   before mapping a local GET timeout so an expired budget yields `read_operation_timeout`.
   Existing parsing/model-conversion deadline boundaries remain as currently documented.
8. Check aggregate deadline/request availability before scheduling another attempt, and keep
   `AdmittedTransport` as the sole physical-attempt charging boundary. If aggregate budget is
   already exhausted, raise its existing error immediately. If a scheduled wait is at least the
   remaining GET deadline, stop with the current failure without sleeping. If the GET timer
   actually expires, return existing `504 upstream_timeout`; an enclosing expired operation
   retains its existing deadline error. Never start a request after a deadline has expired.
9. Exhaustion returns the last attempt's existing mapping. Success after a retry produces no
   caller-visible retry error. Do not retry an `ApplicationError` catch-all or move retry into
   `AsyncHTTPTransport`; leave its `retries=0` for direct and proxy pools.

### HTTP boundary coverage and retry ownership

| Processing boundary | Current source | Retry decision | Required integration behavior |
|---|---|---|---|
| Incoming REST/MCP body, authentication header validation | `api/body_limits.py`, `api/security.py` | No request replay | Invalid/oversized bodies and invalid keys fail before upstream work |
| Identity verification, including MCP connection authentication | `integrations/redmine/identity.py`, `bootstrap.build_authentication` | Covered by central GET retry | Same key and existing authentication budget; invalid upstream credentials fail immediately |
| Reader gateways, metadata and pagination probes | `integrations/redmine/*`, `RedmineClient.get/get_page` | Central retry owner is `get` | Retry only the current GET; prior successful probes/pages are not repeated |
| Capability reports, discovery and writer authorization | `integrations/redmine/capabilities.py`, `auth/capabilities.py`, `mcp/discovery.py` | Covered by central GET retry | Existing enclosing timers and request-local evidence caching remain intact |
| Writer preflight, reconciliation and read-back | Existing writer gateways, including `project_versions.py` | GET retry only | Preserve acceptance/uncertainty after exhausted read-back; no mutation replay |
| Ordered membership read/write batches | `features/projects/membership_service.py` | Current GET can retry | Same batch budget, cooperative remaining time and existing stop/skip/receipt rules |
| Physical network dispatch, direct and environment proxy pools | `integrations/redmine/transport.py` | No transport retry loop | Charge each attempt once; release semaphore before sleep; keep HTTPX `retries=0` |
| MCP-to-REST in-process dispatch and safe error conversion | `app.py`, `mcp/read_limits.py`, `mcp/compatibility.py` | No internal REST retry | Dispatch the REST operation once, preserve its sanitized final error |
| MCP session initialization, JSON-RPC delivery and streamed responses | `mcp/registration.py`, compatibility/lifecycle code, `api/middleware.py` | No automatic session/message replay | Preserve cancellation and session ownership; do not retry after stream headers or duplicate calls |
| JSON/binary mutations and disabled binary download | `integrations/redmine/write.py`, `client.get_attachment_bytes` | No automatic retry | Single mutation attempt; disabled download remains disabled |
| Startup, shutdown and liveness probes | `lifecycle.py`, `api/health.py`, `deploy/compose*.yaml` | No new application retry | Startup creates clients rather than fetching Redmine data; existing Docker health polling is separate |

One identity GET and one feature GET can each take up to three attempts by default, so one
simple REST operation can require six physical upstream requests. This is additive and remains
subject to its aggregate budget; never introduce a second loop that retries the entire REST
operation and multiplies all underlying calls. Completed permission/profile reads retain their
existing request-local caching and refresh rules; failed reads do not create successful evidence.

Keep HTTPX connect/read/write/pool inactivity timeout settings distinct from the whole-GET
deadline, aggregate operation deadline and capability timer. Backoff consumes the same total
GET/parent time. Local `upstream_busy` must not be confused with an eligible native Redmine 503,
and internal application 502 errors must not become a generic MCP retry trigger.

The internal ASGI client has no evidenced timeout conflict requiring an `app.py` change in this
task. Document that its configured HTTPX timeout is not the actual operation timer. Introducing
a network MCP-to-REST hop or new proxy/client timeouts later requires its own timing review.
Deployment outside this repository may impose caller/gateway deadlines; document them when
known, and do not automatically extend them or replay writer requests to accommodate retry.

### Errors

| Scenario | Detection layer | REST status and safe error | MCP result | Retry/reconciliation behavior |
|---|---|---|---|---|
| Invalid caller input | Existing router/service | Existing 422 validation contract | Existing tool error | No retry |
| Missing/invalid caller authentication | Existing authentication | Existing 401 contract | Existing transport/tool boundary | No retry; transient identity GET failures follow eligibility |
| Redmine 401 / 403 / 404 | GET status mapper | 401 `invalid_credentials` / 403 `access_denied` / 404 `resource_not_found` | Existing sanitized tool error | No retry |
| Redmine 400 / 422 or other noneligible unsuccessful status | GET status mapper | Existing 502 `upstream_error` | Existing sanitized tool error | No retry |
| Redmine 429 / 502 / 503 / 504 | GET attempt loop, then existing mapper | Respectively 502 `upstream_rate_limited` / 502 `upstream_error` / 502 `upstream_unavailable` / 504 `upstream_timeout` | Existing sanitized tool error | Bounded retry, then final mapping |
| Eligible transport failure | GET attempt loop, then existing mapper | Existing 502 `upstream_unavailable` or 504 `upstream_timeout` | Existing sanitized tool error | Bounded retry |
| Pool/admission saturation | Existing client/transport | 503 `upstream_busy` | Existing sanitized tool error | No retry |
| Invalid JSON, envelope, model or attachment metadata | Existing parser/gateway | 502 `upstream_response` | Existing sanitized tool error | No retry |
| Oversized response | Existing streamed read | 502 `upstream_response_too_large` | Existing sanitized tool error | No retry |
| Exhausted request/byte budget or operation deadline | Existing budget | 422 `scan_budget_exceeded` / 504 `read_operation_timeout` | Existing sanitized tool error | No retry and no reset |
| Cancelled request | Existing async boundary | Existing cancellation behavior | Existing stream/session behavior | Propagate cancellation; close response and stop dispatch |

### Write semantics

No new write behavior. POST/PUT/PATCH/DELETE, JSON writes and binary uploads remain single
attempt. Preserve accepted/uncertain receipts, dispatch tracking, and independent read-back.
Eligible GETs in writer authorization/preflight/read-back use the read retry policy. Failed
read-back still cannot prove the mutation failed; never replay the mutation. Membership batches
charge retry attempts to their existing dedicated budget and retain stop/skip semantics.
No new synthetic state or cleanup requirement is introduced beyond the existing writer fixtures.

Specification exit check: policy, scope, settings, errors and compatibility are decided.
Implementation/review are finished; authorized runtime evidence is recorded in section 7.

## 5. Implementation plan

| Step | Concrete change | Files/components | Depends on | Verification |
|---|---|---|---|---|
| 1 | Review eligibility and existing error/deadline behavior against this contract | Task and current adapter/budget code | Existing accepted baseline | Source review |
| 2 | Add validated settings and read policy fields; forward through bootstrap | `config.py`, `integrations/redmine/policy.py`, `bootstrap.py` | 1 | Configuration scenarios in TEST-005 |
| 3 | Add typed retry classification, delay/header parsing and timing helpers | New `integrations/redmine/retry.py` | 2 | TEST-001..006, after testing authorization |
| 4 | Refactor streamed GET acquisition into bounded attempts under one deadline | `integrations/redmine/client.py` | 3 | TEST-001..004/006/007 |
| 5 | Preserve admitted transport charging/cleanup; expose non-charging budget availability and remaining time for GET acquisition/backoff, including cooperative batches | `integrations/redmine/transport.py`, `common/read_budget.py` | 4 | TEST-003/007/012; no hidden transport retry or whole-writer timer |
| 6 | Add safe INFO retry events with attempt, next attempt, delay and allowlisted status/reason only | `client.py`, `constants/logs.py` if needed | 4 | TEST-008; request ID retains existing correlation |
| 7 | Document settings, timing hierarchy, internal ASGI timeout limitation, eligible GETs and single-attempt mutations | `.env.example`, `docs/configuration.md`, `docs/architecture.md`, `docs/tool-reference.md`, `docs/manual-verification.md`, `CHANGELOG.md` | 2..6 | Manual source/prose review |
| 8 | Implement and execute the separate verification handoff | Future tests and evidence report | Explicit testing assignment, completed code | Section 7 scenarios |

No service, Protocol, router, allowlist, mutation transport or public response schema change is
required. No new dependency is planned; use stdlib timing/header parsing and existing HTTPX.
If implementation introduces a dependency, review it explicitly and update `pyproject.toml`
with `uv.lock` together. No deployment, seed, reset, or production fault injection is authorized.

## 6. Acceptance criteria and traceability

| Criterion ID | Given | When | Then |
|---|---|---|---|
| AC-001 | Eligible GET failure followed by success | Existing reader or identity lookup runs | Exact GET retries and returns the usual model without replaying earlier calls |
| AC-002 | Persistent eligible failure | Attempt cap is reached | No extra dispatch; final existing safe error is returned |
| AC-003 | Noneligible failure or mutation | Configured attempts exceed one | No automatic replay; invalid data and uncertain writes retain current semantics |
| AC-004 | Backoff/header delay and constrained capacity/budget | Another attempt is considered | Delay policy is obeyed, response closes, capacity is released, and limits are never reset |
| AC-005 | Attempt config of one or invalid settings | Client starts or is called | One disables retries; invalid bounds/nonfinite values fail settings validation |
| AC-006 | Cancellation/deadline/partial body | Attempt or backoff is interrupted | Dispatch stops; buffers are discarded, prior bytes remain charged, responses close |
| AC-007 | Concurrent callers and REST/MCP calls | Transient failures occur | Each caller retains its key; result/error schemas, permissions and safe logs remain compatible |
| AC-008 | A complete REST/MCP operation, capability timer or cooperative batch | GETs retry or parent time runs out | Each operation dispatches once, only its failed GET repeats, parent deadline wins, and earlier write receipts survive |

| Requirement | Acceptance criterion | Verification method | Evidence | Result |
|---|---|---|---|---|
| REQ-001 | AC-001, AC-002 | TEST-001/002/009 | EVID-003; testing report scenario mapping | Pass |
| REQ-002 | AC-003 | TEST-004/010 | EVID-003; mutation and malformed-data cases | Pass |
| REQ-003 | AC-004, AC-006 | TEST-003/006/007 | EVID-003; budget, delay and cleanup cases | Pass |
| REQ-004 | AC-005 | TEST-005 | EVID-003; settings/bootstrap/Compose cases | Pass |
| REQ-005 | AC-007 | TEST-008/009/010/011 | EVID-003/004; isolation, REST/MCP and owned reader parity | Pass |
| REQ-006 | AC-008 | TEST-009/010/012 | EVID-003; dispatch, capability/batch deadline and ASGI cases | Pass |

## 7. Test plan and execution record

### Scenario plan

These scenarios originated as a future handoff. After implementation, the user explicitly
assigned testing on 2026-10-07. Execution is recorded in
[PREP-027 testing](../../testing/evidence/prep-027-testing.md). Reuse the existing
offline pytest/pytest-asyncio baseline, fake settings, HTTPX MockTransport, explicit ASGI lifespan
and MCP SDK clients. Use controlled clocks/sleep/randomness rather than long real waits.

| Scenario ID | Acceptance criteria | Layer/method | Setup and input | Expected result | Offline/live |
|---|---|---|---|---|---|
| TEST-001 | AC-001 | Adapter | Parameterize every eligible exception/status, then valid 200; include streamed read failure and page probe | Success, correct attempt count, fresh buffer/request and unchanged params | Offline |
| TEST-002 | AC-002 | Adapter + REST/MCP | Eligible failures persist or change between attempts | Cap obeyed; final failure mapping retained | Offline |
| TEST-003 | AC-004/006 | Transport/budget | Retry with low request/byte limits and a membership batch budget | All attempts charged once; partial bytes accumulate; exhaustion stops dispatch | Offline |
| TEST-004 | AC-003 | Adapter | 3xx/400/401/403/404/422/500, invalid JSON/model/attachment URL, oversized body, pool/admission timeout | One attempt; current errors retained | Offline |
| TEST-005 | AC-005 | Settings/wiring | Defaults, one attempt, upper bound, invalid integer/nonfinite/base > cap; identity and feature construction | Defaults align and settings propagate; invalid startup rejected | Offline |
| TEST-006 | AC-004 | Delay helpers + adapter | Backoff/jitter bounds; valid integer/date headers, past date, zero, missing/invalid/multiple headers, excessive delay | Exact policy; never retry early for valid header; close before wait | Offline |
| TEST-007 | AC-004/006 | Async transport | Cancellation while waiting/sending/reading/closing; GET or outer deadline expires; permit concurrency one | No leaked permit, later retry or reset deadline; cleanup completes | Offline |
| TEST-008 | AC-007 | Logging/session isolation | Two keys, shared pool, cookies/default auth and sensitive URL/header/body/exception content | Same key per attempt; no sensitive log values; safe reason and correlation only | Offline |
| TEST-009 | AC-001/002/007 | REST + MCP | Existing `get_issue`, list pagination, identity/discovery/authorization failures then recovery/exhaustion | Same schemas/IDs/permissions and final error boundary | Offline |
| TEST-010 | AC-003/007 | Writer + batch integration | JSON/binary mutation failure; transient preflight/read-back GET; accepted write then exhausted read-back | One mutation; accepted/uncertain receipts and batch stopping retained | Offline |
| TEST-011 | AC-007 | Startup + Inspector | Owned pinned 7.0.2 reader; separate permitted writer fixture only if write checks selected | Existing valid reads and permissions remain compatible; no unsolicited mutations | Opt-in synthetic live |
| TEST-012 | AC-004/006/008 | Budget + REST/MCP + writer integration | Short reader/capability parent timer; cooperative batch near expiry during backoff/admission/GET stream after an accepted mutation; shorter configured internal ASGI timeout | One internal REST/tool dispatch; no multiplied attempts or timeout reset; existing deadline mapping; accepted mutation receipt retained; no whole-batch cancellation | Offline |

Coverage selection: defaults/configuration TEST-005; exact encoding/mapping/pagination TEST-001/009;
invalid inputs and malformed responses TEST-004/009; authentication/permissions TEST-008/009/011;
MCP discovery/invocation/errors TEST-009/011; writes/uncertainty TEST-010; cleanup TEST-007/011.
Empty legitimate responses use existing model fixtures in TEST-009. Binary download remains
disabled. Live transient failures, if needed, use a task-owned fault wrapper outside Redmine
and require a separate explicit verification assignment; do not disrupt production or shared hosts.

### Execution evidence

| Evidence ID | Command/procedure and environment | Scenario/check | Expected | Actual redacted result | Status | Date |
|---|---|---|---|---|---|---|
| EVID-001 | Source and documentation inspection through Git Bash | Planning baseline | Identify shared GET, writer and budget boundaries | Inspected current source; no runtime claims | Recorded | 2026-10-07 |
| EVID-001A | Read runtime dispatch sites, middleware, capability/batch code and installed HTTPX ASGI transport through Git Bash | HTTP boundary follow-up | Identify missing retry paths and deadline interactions | Central GET covers all current upstream reads; cooperative batch remaining time and internal ASGI timeout distinction added to plan | Recorded | 2026-10-07 |
| EVID-002 | `uv run --frozen --no-sync ruff check .`; `uv run --frozen --no-sync ruff format --check .`; `uv run --frozen --no-sync mypy src`; `git diff --check`, through Git Bash | Static checks | Lint/format/type/diff checks pass | Ruff passed; 278 files already formatted; mypy passed for 124 source files; diff check passed with line-ending notices only | Pass | 2026-10-07 |
| EVID-003 | Focused, full regression and final targeted pytest commands in [testing report](../../testing/evidence/prep-027-testing.md) | TEST-001..010 and TEST-012 | New scenarios and relevant regressions pass | 103 focused passed; full run 1,457 passed/41 old assertion failures; all 41 resolved in 92 passing final targeted cases, reconciled by XML case ID | Pass after corrections | 2026-10-07 |
| EVID-004 | Selected owned live pytest and `scripts/verify-read-retries-inspector.py`; exact commands in testing report | TEST-011 | Successful invocation and preserved permission boundaries | 2 live tests; reader startup, discovery and 3 Inspector reads passed; zero live mutations | Pass | 2026-10-07 |
| EVID-005 | `uv build`, only if packaging/dependencies change and checks are authorized | Build | Source/wheel build succeeds | N/A for planned dependency-free change | Conditional | N/A |

Limitations: eligible failures and writer uncertainty are injected offline. Live checks cover
ordinary owned reader compatibility, without live mutations or fault injection. No build,
deployment, seed or reset was performed. Full regression evidence is a completed run plus final
targeted reruns of every modified function; no clean full-suite rerun is claimed after test edits.

## 8. Implementation and review record

The following coding-stage record is retained as history. The later authorized testing stage
is recorded below and supersedes its pending verification statements.

- Changes made: shared streamed GET attempts in `integrations/redmine/client.py`, injectable
  eligibility/backoff/header helpers in `retry.py`, retry fields in `ReadPolicy` and validated
  `Settings`, bootstrap forwarding, non-charging budget admission/absolute deadline helpers,
  and safe retry log constants. Direct/proxy transport retries remain disabled; writer
  dispatch, public operations/models and permission gates retain their existing contracts.
- Review fixes: removed fixed 64 KiB decoded chunk buffering so a short failed tail is charged;
  use the budget's absolute monotonic cutoff rather than reconstructing a deadline from two
  samples; forward all three retry environment variables through both Compose services.
- Plan deviations: added Compose environment forwarding after implementation review found
  operator `.env` overrides would otherwise be ignored in containers. This is configuration
  wiring only; no deployment or live configuration was performed. Task/roadmap tracking is
  synchronized. No new runtime dependency or lockfile change was needed.
- Follow-up review requested by the user: audited all runtime HTTP dispatch layers. Added a
  coverage/ownership matrix, cooperative batch remaining-time handling, internal ASGI timeout
  clarification and TEST-012. No additional retry loop or separate runtime task is needed.
- Quality results: EVID-002 passed after explicit user authorization. An earlier Ruff attempt
  was rejected by automatic approval review under the previous source-only restriction;
  no passing result was inferred from interrupted calls. Automated tests remain EVID-003 pending.
- Startup and Inspector results: EVID-004 pending.
- Documentation updated: `.env.example`, configuration, architecture, tool reference,
  manual-verification guide, changelog, task and roadmap. Config/deadline descriptions include
  Compose forwarding, internal ASGI timing limitations and preserved mutation receipts.
- Final diff review: retry scope, status mappings, response closure, caller-key isolation,
  unchanged writer transport and retained unrelated bug/index edits inspected manually.
  Ruff/format/mypy/diff checks report no failures; no test files were changed.
- Pre-existing failures versus introduced failures: the three code/config review findings were
  corrected in source; their runtime regression evidence remains pending. Bug-001 remains
  unresolved and is not closed by this task.
- Testing handoff: create deterministic clock/sleep/jitter and streamed-response fixtures for
  TEST-001..010 and TEST-012. Cover a failed decoded tail shorter than 64 KiB, retries after
  partial data consuming the same byte budget, exact parent cutoff/error precedence, cancellation
  and cleanup failures, repeated/date Retry-After headers, and Compose forwarding including
  attempts `1`. Coordinate the injected GET monotonic clock with the budget clock when testing
  absolute deadlines. Update prior single-attempt expectations only where the new GET policy
  intentionally changes them; explicitly use attempts `1` for tests isolating old error mappings.
  Reuse offline fake settings, HTTPX MockTransport/ASGI lifespan/MCP clients and existing
  restricted writer fixtures. Test exhausted read-back after an accepted mutation and no
  repeated mutations. TEST-011 requires the owned pinned 7.0.2 synthetic environment and
  explicit startup/Inspector/live authorization; any writer fixtures require owned cleanup.
- Remaining blocker: separately authorized test implementation, execution and synthetic
  compatibility evidence. Coding is finished; no acceptance criterion is marked passed.

### Subsequent authorized testing stage

- Added deterministic timing/observable streams in `tests/retry_helpers.py`, unit retry cases,
  REST/MCP retry integration cases, selected owned reader E2E cases and a read-only Inspector
  harness. The 103 focused offline scenarios pass, including review regressions for decoded
  partial tails and exact absolute budget cutoffs.
- Adapted existing reader error contract request counts for eligible 429/503/504 failures,
  including profile timeout/connection errors, preserving one authentication call, identical
  retry URLs/parameters and unchanged final error mappings. All 81 parameterizations of the
  three adapted functions pass on their final rerun.
- Owned live reader checks (2 cases), startup and Inspector discovery/three read calls pass.
  No Redmine resources were created or mutated. The temporary reader and credential config
  are cleaned up by the harness.
- New fixtures were corrected as documented in the testing report. Runtime implementation
  did not change during verification. The full suite completed with 1,457 passes and 41 obsolete
  single-attempt assertions. All 35 reader/profile failures are covered by the 81 passing adapted
  cases; the remaining 6 foundation failures are covered by 11 passing cases after explicit
  retry-disable configuration. XML case IDs confirm all failures were resolved. Existing
  runtime default retries and test coverage are retained; no blanket disabling or deletion.
- Ruff, formatting, mypy and the architecture gate pass; exact results and commands are in
  [PREP-027 testing](../../testing/evidence/prep-027-testing.md). Bug-001 remains separately
  blocked on the original sanitized malformed upstream payload.

## 9. Completion and handoff

Follow-up review fix (2026-10-07): moved Inspector credential deletion to an outer
`try/finally` covering configuration creation, chmod, log opening, process startup and
shutdown exceptions. Added nine passing offline cleanup regression cases and passed scoped
Ruff formatting/lint, mypy and diff checks. No runtime retry changes or repeated live checks.
Details are in the testing report's follow-up review section; prior acceptance history is retained.

- [x] Required behavior implemented in source and exercised by focused runtime cases.
- [x] Every requirement has passing acceptance evidence.
- [x] Relevant automated tests and repository checks pass, using full results plus final targeted corrections.
- [x] Required synthetic startup/Inspector compatibility verification completed.
- [x] Runtime documentation reflects the implemented behavior and verification limits.
- [x] Implementation review confirms no unresolved decision changes the specified behavior.
- [x] Final implementation diff reviewed and task record synchronized.

Final status: **complete**.

Outcome: bounded, configurable Redmine GET retry implemented with shared deadline/budget,
immediate decoded-byte accounting and local/container configuration. Focused tests and owned
live/Inspector checks pass; every full-run assertion failure is resolved by final targeted evidence.
Existing malformed-data investigation retains its separate owner.

Next action: none for PREP-027. For Bug-001, obtain the original sanitized upstream response and
exact arguments; generic malformed-data errors are intentionally not retried.
