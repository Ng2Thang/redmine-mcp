# prep-015: Limit pagination scans and concurrent Redmine requests

## 1. Task identity and status

| Field | Value |
|---|---|
| Task ID | prep-015-bounded-redmine-reads |
| Assigned capability | Explore bounded Redmine pages and retrieve attachment links without binary transfers |
| Type | Shared runtime prerequisite; extend existing readers |
| Access | Read policy; shared transport admission also covers writes |
| Destructive effects | None |
| Status | blocked |
| Dependencies | Existing prep-003/005/010-013 and tool-031 implementations; prep-002 offline baseline for later testing |
| Related tasks | tool-001, tool-012, tool-017, tool-018, tool-019, tool-031 |
| Target Redmine version | Redmine 7.0.2; runtime acceptance pending |
| Last updated | 2026-10-05, Codex |
| Progress summary | Implementation finished; Ruff lint/format, mypy and whitespace checks pass; runtime acceptance pending |
| Next action | Obtain a separate testing assignment for TEST-001 through TEST-006; update existing paging/download expectations without changing prior evidence |

## 2. Discovery and evidence

The current runtime limits each page to 100 records but permits repeated pagination.
Capability inventory loops allow 100 pages. Per-upstream deadlines and payload bounds do not
establish an aggregate read budget. The existing download tool transfers base64 file content.
Repository instructions require English Markdown, Git Bash, and separately authorized testing.
The working tree was clean before this task. No existing test files may be changed.

Sources: `common/pagination.py`, Redmine gateways, runtime lifespan, MCP registration/discovery,
and the pinned Redmine 7.0.2 deployment. No new upstream endpoint or permission is introduced.
[Redmine REST pagination](https://www.redmine.org/projects/redmine/wiki/Rest_api), read on
2026-10-05, documents default 25 / maximum 100 and `total_count`; live behavior is unverified.

Decisions: no user quota, query token, persistent query state, result cache, statistics tool,
generated export, or background job. One process semaphore covers outgoing requests.
Oversized query discovery is allowed only at offset zero. Attachment retrieval is link-only.

## 3. Requirements

| ID | Required observable behavior |
|---|---|
| REQ-001 | One lifespan-owned semaphore bounds all outgoing Redmine requests until response closure |
| REQ-002 | REST/MCP readers share aggregate request, byte, and elapsed-time budgets across nested authentication and containers |
| REQ-003 | First pages report pagination policy; subsequent pages require at most the configured number of matching pages |
| REQ-004 | Capability inventories obey bounded scans and never treat incomplete evidence as denial |
| REQ-005 | REST and cached MCP download calls transfer no bytes; metadata returns validated public attachment links |
| REQ-006 | Safe policy errors and documentation explain intentional compatibility changes |

## 4. Public contract and technical specification

Existing reader names, page default 25 / maximum 100, filters, and ordering remain stable.
For issues, projects, issue time entries, and project capabilities, add `pagination_policy`
with `total_pages = ceil(total / limit)`, `max_query_pages`, and `requires_narrowing`.
At offset zero return a discovery page even if its total exceeds the configured ceiling.
For positive offsets reject `offset + limit > max_query_pages * limit` before collection access;
probe the same filtered collection at offset zero / limit one, reject an oversized total, then
fetch the requested page. Recheck its total for concurrent growth. No cross-call state is stored.
Capability filters requiring complete inventory must reject oversized inventories and request
`project_id`. Existing tools without narrowing filters can become unavailable beyond a preview.

| Setting | Default |
|---|---:|
| REDMINE_MAX_CONCURRENT_REQUESTS | 50 |
| REDMINE_ADMISSION_TIMEOUT_SECONDS | 30 |
| REDMINE_MAX_QUERY_PAGES | 10 |
| REDMINE_READ_OPERATION_MAX_REQUESTS | 30 |
| REDMINE_READ_OPERATION_DEADLINE_SECONDS | 90 |
| REDMINE_READ_OPERATION_MAX_BYTES | 10485760 |
| REDMINE_PUBLIC_URL | Unset; use upstream base URL |

Counts are positive integers; times are positive finite values. Semaphore acquisition precedes
physical dispatch and has a bounded wait. Release after closure on success, error, timeout, or
cancellation. Aggregate read deadlines include auth, admission, acquisition, and conversion.
Nested REST requests inherit the current budget. Transport authentication is independently
bounded; logical MCP tool/discovery handlers create fresh budgets rather than inheriting an
expired connection context. Writer invocations do not receive aggregate cancellation deadlines.

| Scenario | REST code/status | MCP behavior |
|---|---|---|
| Admission timeout | upstream_busy / 503 | Safe tool error |
| Request/byte budget exhausted | scan_budget_exceeded / 422 | Safe tool error |
| Aggregate deadline | read_operation_timeout / 504 | Safe tool error |
| Broad/deep query | scope_required / 422 | Safe tool error with narrower-scope guidance |
| Attachment content request | attachment_download_disabled / 403 | Cached tool invocation rejected |

Retain `error.code` / `error.message`; MCP tool failures have `isError=true`. Discovery retains
its existing protocol error path. Remove download_attachment from the MCP allowlist and reject
its REST route before auth/upstream work. Validate attachment URLs against configured Redmine
origin and download path before replacing the base with optional REDMINE_PUBLIC_URL. Links
contain no credentials; browser authentication remains necessary. Return only existing visible
files. N/A for new writes, generated exports, administrative seeding, or direct database access.

## 5. Implementation plan

1. Add settings, lifespan-owned transport admission, and safe stream cleanup.
2. Add framework-independent budget context; wire REST, MCP read dispatch/auth/discovery.
3. Implement shared pagination checks and bounded capabilities inventory logic.
4. Disable binary delivery; map validated attachment links to a public base URL.
5. Update configuration, deployment/environment examples, tool reference, changelog, and roadmap.
6. Run installed Ruff lint/format checks and mypy; inspect the final diff.

No dependency changes, testing infrastructure, tests, or fixtures are authorized.

## 6. Acceptance criteria and traceability

| Criterion | Requirement | Expected behavior | Evidence |
|---|---|---|---|
| AC-001 | REQ-001 | With more than the configured concurrency limit attempting requests, active responses never exceed that limit (at least 51 attempts for default 50); cancellation/closure release permits | Pending TEST-001 |
| AC-002 | REQ-002 | Nested auth, probes and features share limits; exhaustion stops dispatch; writer outcomes remain intact | Pending TEST-002 |
| AC-003 | REQ-003 | Million-record preview reports narrowing; continuation rejected; narrowed queries and boundary pages succeed | Pending TEST-003 |
| AC-004 | REQ-004 | Large capabilities inventory stops before scanning; changing/incomplete evidence never proves denial | Pending TEST-004 |
| AC-005 | REQ-005 | Direct/cached download calls fetch no bytes; metadata links are usable and credential-free | Pending TEST-005 |
| AC-006 | REQ-006 | REST/MCP errors recognizable, successful contracts compatible, documentation updated | Pending TEST-006 |

## 7. Test plan and execution record

All scenarios are handoffs, not authorization to create or execute tests.

| Scenario | Planned verification |
|---|---|
| TEST-001 | HTTPX MockTransport admission contention, admission timeout, stream errors, cancellation and repeated closure |
| TEST-002 | ASGI lifespan and MCP SDK nested budgets, exact request/byte/time boundaries, auth isolation, writer pre-dispatch denial and post-write read-back failure |
| TEST-003 | Empty/boundary/million-record totals, same-filter probes, deep/nonaligned offsets, limit changes and concurrent growth |
| TEST-004 | Project inventory bound, total changes, missing metadata, duplicate pages, unknown evidence and scoped project filtering |
| TEST-005 | Disabled REST/cached MCP calls, invalid URL origins/traversal, public subpaths and metadata-only project/issue file retrieval |
| TEST-006 | SDK discovery, tool isError envelopes, original valid read contracts, opt-in synthetic Inspector and browser links |

Runtime execution evidence: pending. No tests, build, startup, Inspector, live calls, or seeding run.
Required later tooling: existing pytest/pytest-asyncio, HTTPX MockTransport, explicit ASGI lifespan,
MCP SDK client; synthetic browser/Inspector checks require separate authorization.

## 8. Implementation and review record

Implementation finished on 2026-10-05. Shared transport admission is created with the lifespan
upstream client and holds permits through response closure. Shielded, single-task stream cleanup
retains permits during cancellation and avoids double release. Physical dispatch is marked in
request extensions so a writer timeout during admission does not imply a mutation was sent.
Existing dispatched-write uncertain receipts and read-back results are preserved.

REST middleware starts read budgets before identity lookup; MCP raw SDK handlers start fresh
read/discovery budgets and clear inherited authentication context for writers. SDK schemas are
seeded before dispatch. The internal ASGI HTTP client converts safe REST errors before adapter
exception conversion, so tool errors preserve their code/message without validation body values.
This adapter remains tied to the pinned FastAPI-MCP 0.4.0 / MCP SDK 1.30.0 integration.

Issues/projects/time entries use one shared same-filter metadata gate, with a post-fetch total
check. Capability listings enforce depth and bound complete-inventory filters. Discovery returns
incomplete inventory evidence for oversized projects, preserving unknown candidates instead of
proving denial; tools/list has no project filter. Default logical budgets can stop an internal
scan before the page ceiling because authentication, metadata and role lookups also consume work.

Attachment content is rejected at middleware, REST, service and gateway boundaries; cached tool
invocations are explicitly blocked and download capability candidates are removed. Attachment
links in JSON metadata are validated before optional public-origin/subpath mapping. The disabled
content route is hidden from OpenAPI. No additional operations, dependencies or lockfile changes.

Updated English docs: configuration, architecture, tool reference, manual verification,
changelog, this task and roadmap; environment and both deployment listeners expose settings.
Source/diff review covered credential isolation, bounded scans, unknown permission evidence,
stream cancellation, writer dispatch uncertainty, and intentional download/paging compatibility.
The initial working tree was clean. No tests, fixtures or testing infrastructure were changed.

| Evidence | Command (Git Bash) | Result | Date |
|---|---|---|---|
| STATIC-001 | `.venv/Scripts/ruff.exe check .` | Passed | 2026-10-05 |
| STATIC-002 | `.venv/Scripts/ruff.exe format --check .` | Passed; 196 files formatted | 2026-10-05 |
| STATIC-003 | `.venv/Scripts/python.exe -m mypy src` | Passed; 111 source files | 2026-10-05 |
| STATIC-004 | `git diff --check` | Passed; Git emitted line-ending normalization notices only | 2026-10-05 |

Initial static checks found import/format errors and an untyped FastApiMCP subclass; these were
resolved with scoped formatting and a typed HTTPX internal client plus typed SDK callbacks.
Static checks provide no runtime acceptance evidence. TEST-001 through TEST-006 remain pending.

### Review fixes on 2026-10-05

The follow-up source review identified two defects, and the user authorized code/document fixes.
REST response-start deadline errors could pass through Starlette's already-started exception
sender and become `500 internal_error`. Middleware now discards the expired pending response
without buffering it and raises the captured error at its own boundary, preserving
`504 read_operation_timeout` before any client headers are sent, including inherited budgets.

The custom HTTPX transport disabled automatic environment proxy routing. The client now builds
explicit mounts using the pinned HTTPX environment-proxy parser; proxy transports and the direct
transport receive one shared lifespan-owned semaphore. `NO_PROXY` mounts fall back to the admitted
direct transport. This intentionally uses HTTPX's internal parser to preserve its platform proxy
semantics; reassess that integration when upgrading HTTPX. No dependency changes were required.

Prior implementation changes were preserved. Configuration, architecture, manual verification,
changelog and roadmap document these fixes. Follow-up static checks passed; runtime evidence
remains pending. Final source/diff inspection confirmed all proxy mounts use the same semaphore,
deadline errors are rendered before external headers, and earlier working-tree changes remain.

| Evidence | Command (Git Bash) | Result | Date |
|---|---|---|---|
| STATIC-005 | `.venv/Scripts/ruff.exe check .` | Passed | 2026-10-05 |
| STATIC-006 | `.venv/Scripts/ruff.exe format --check .` | Passed; 196 files already formatted | 2026-10-05 |
| STATIC-007 | `.venv/Scripts/python.exe -m mypy src` | Passed; 111 source files | 2026-10-05 |
| STATIC-008 | `git -c core.safecrlf=false diff --check` | Passed | 2026-10-05 |

The later testing assignment must include pre-header synchronous deadline expiration in
REST/MCP (TEST-002), environment HTTP/HTTPS/ALL proxy routing and `NO_PROXY` bypass, plus shared
direct/proxy admission and cleanup (TEST-001). These are handoff cases, not executed evidence.

### Approved default changes on 2026-10-05

The user authorized default concurrency 50, admission wait 30 seconds, logical-read request
budget 30 and aggregate deadline 90 seconds. The settings table above reflects these values,
superseding the original 10 / 1 / 10 / 15 defaults. Runtime settings, the framework-independent
read policy, `.env.example` and both Compose listeners now agree. Query pages remain 10 and
aggregate read bytes remain 10 MiB; individual upstream timeouts are unchanged.

The deadline is shared across all admission waits and processing within a read. It does not
reserve a separate 60-second processing window after admission. Existing explicit environment
values override the new defaults; local `.env` files were not modified. Previously edited files
and unrelated Azurite state files were preserved. No tests or runtime verification were run.
TEST-001/TEST-002 need updated default expectations and separately authorized contention,
nested-budget and timeout verification. The 50-request default has no load-capacity evidence yet.

Final source inspection confirmed the four approved defaults agree across code, environment
example and both Compose services. Static checks for this follow-up passed:

| Evidence | Command (Git Bash) | Result | Date |
|---|---|---|---|
| STATIC-009 | `.venv/Scripts/ruff.exe check .` | Passed | 2026-10-05 |
| STATIC-010 | `.venv/Scripts/ruff.exe format --check .` | Passed; 196 files already formatted | 2026-10-05 |
| STATIC-011 | `.venv/Scripts/python.exe -m mypy src` | Passed; 111 source files | 2026-10-05 |
| STATIC-012 | `git -c core.safecrlf=false diff --check` | Passed | 2026-10-05 |

### Pagination guidance and acceptance review fixes on 2026-10-05

The user authorized both follow-up findings. The time-entry route description now instructs
REST/MCP callers to check pagination policy, stop on scope/budget errors, and label incomplete
totals partial or unavailable. The tool reference's issue-list and aggregation examples follow
the same contract. They disclose narrowed scope and avoid promising unsupported time-entry date
filters. Operation IDs, runtime policy and configured defaults are unchanged.

AC-001 now follows the configured concurrency limit; default 50 requires at least 51 attempts
to create contention. Manual verification, changelog and roadmap are synchronized. No tests,
fixtures, runtime checks or unrelated working-tree files were changed. TEST-001 needs configured
limit contention coverage; TEST-006 needs generated description and partial-total guidance
checks during a separately authorized verification assignment. Acceptance evidence remains pending.

Final source/document inspection confirmed the reviewed unconditional scan instructions and old
ten-request acceptance wording were removed. Static checks passed for this follow-up:

| Evidence | Command (Git Bash) | Result | Date |
|---|---|---|---|
| STATIC-013 | `.venv/Scripts/ruff.exe check .` | Passed | 2026-10-05 |
| STATIC-014 | `.venv/Scripts/ruff.exe format --check .` | Passed; 196 files already formatted | 2026-10-05 |
| STATIC-015 | `.venv/Scripts/python.exe -m mypy src` | Passed; 111 source files | 2026-10-05 |
| STATIC-016 | `git -c core.safecrlf=false diff --check` | Passed | 2026-10-05 |

### User-reported settings import failure on 2026-10-05

The user's Uvicorn traceback showed Pydantic failing to construct `Settings` during import with
`validator-signature`. The `empty_public_url` validator was decorated as a classmethod but
declared only `value`; binding consumed that argument and left an empty callable signature.
The fix adds `cls` before `value`, matching the existing log-level validator. Empty public URL
normalization and approved configuration defaults are unchanged.

Previous source reviews and passing static checks missed this runtime defect. The supplied
traceback is failure evidence; it is not successful verification of the fix. No application
import, startup, tests or Inspector checks were executed for this coding fix. TEST-002/TEST-005
must cover settings construction with omitted, empty and valid public URLs, and TEST-006 must
cover application startup during separately authorized verification. Changelog records the fix;
runtime acceptance remains pending.

Static checks after the validator fix:

| Evidence | Command (Git Bash) | Result | Date |
|---|---|---|---|
| STATIC-017 | `.venv/Scripts/ruff.exe check .` | Passed | 2026-10-05 |
| STATIC-018 | `.venv/Scripts/ruff.exe format --check .` | Passed; 196 files already formatted | 2026-10-05 |
| STATIC-019 | `.venv/Scripts/python.exe -m mypy src` | Passed; 111 source files | 2026-10-05 |
| STATIC-020 | `git -c core.safecrlf=false diff --check` | Passed | 2026-10-05 |

## 9. Completion and handoff

- [x] Required behavior implemented.
- [x] Static checks pass and final diff reviewed.
- [ ] Every acceptance criterion has passing runtime evidence.
- [x] Documentation reflects final behavior.
- [x] Task and dashboard synchronized.

Final status: **blocked - implementation finished; testing pending**.
Next action: separately authorize TEST-001 through TEST-006 with the existing offline baseline;
follow with explicitly authorized synthetic startup/Inspector/browser-link acceptance. Existing
download-tool tests and paging/schema expectations require updates during that testing assignment.

No request-rate or per-user fairness guarantee: repeated previews and different small queries
remain possible. Metadata counts still have upstream cost. Limits are per process; independent
workers/deployments have independent semaphores. No distributed admission control is included.
