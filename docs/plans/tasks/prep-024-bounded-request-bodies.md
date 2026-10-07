# prep-024-bounded-request-bodies: Reject oversized input before JSON parsing

## 1. Task identity and status

| Field | Value |
|---|---|
| Task ID | prep-024-bounded-request-bodies |
| Assigned capability | Submit bounded attachment/tool inputs without allowing oversized JSON bodies to consume unbounded application buffering |
| Type / access | Shared REST/MCP admission prerequisite; existing readers and restricted writers |
| Destructive effects | Planning has none; accepted writer calls retain their existing effects |
| Status | blocked - implementation finished; testing pending |
| Dependencies | Existing upload contract and request middleware; selected baseline in [prep-020](prep-020-current-catalog-acceptance.md) |
| Related tasks | tool-020, prep-015, prep-016/017; [dashboard](../index.md); prep-026 |
| Target Redmine version | 7.0.2; body admission is local and new behavior is unverified |
| Last updated | 2026-10-07, Codex |
| Progress summary | ASGI admission, derived cap and public documentation implemented; Ruff/mypy checks pass; BODY-024 acceptance pending |
| Next action | Separately authorize BODY-024-001..006 test implementation and offline/startup/Inspector/owned live verification |

## 2. Discovery and evidence

`UploadRequest.content_base64` has only a minimum length. The service correctly checks encoded
and decoded size, but framework JSON parsing occurs first. A very large REST or MCP request can
therefore be read and parsed before the service rejects it. This review identifies where the
limit applies; it did not perform a load test or claim a measured memory failure.

| Source | Inspected | Evidence / limitation |
|---|---|---|
| `features/attachments/models.py`, `service.py`, `write_router.py` | 2026-10-07 | Encoded bound is enforced inside service; decoded binary default is 5 MiB |
| `app.py`, `api/middleware.py`, `api/read_limits.py` | 2026-10-07 | Request context/read budgets exist; no body-byte admission middleware |
| Installed Starlette `requests.py`, FastAPI routing behavior | Existing request pipeline; inspect during coding | Byte admission must precede JSON materialization, SDK parsing and upstream authentication |
| [Redmine REST API](https://www.redmine.org/projects/redmine/wiki/Rest_api), [current ledger](../current-catalog-acceptance.md) | 2026-10-07 | Native upload uses an existing binary endpoint and temporary token; this plan does not change it |
| `deploy/compose.test.yaml`, `config.py` | 2026-10-07 | Pinned 7.0.2 and existing request/binary response limits |

Clean planning baseline: `36ff5f0`. Keep Git Bash, English Markdown, caller-key isolation, existing
writer gates and explicit verification authorization. Current source is enough to specify the
local admission change; no new native Redmine permission evidence is required.

| Decision | Resolution | Blocking? |
|---|---|---|
| DEC-001 | Use pure ASGI middleware to bound actual received bytes before parsing | No |
| DEC-002 | Apply the same boundary to public MCP POSTs and REST mutation requests, including internal MCP-to-REST calls | No |
| DEC-003 | Keep encoded/decoded service checks as independent semantic limits | No |
| DEC-004 | Do not attempt to decompress request bodies; reject non-identity content encoding | No |

## 3. Requirements

| ID | Required observable behavior | Constraint |
|---|---|---|
| REQ-001 | Bodies above the configured byte cap are rejected before parser/SDK/authentication dispatch | Count bytes, not characters or declared length alone |
| REQ-002 | Missing length, chunked input and understated length cannot bypass the cap | Stop consuming once oversized; no retained full oversized buffer |
| REQ-003 | Valid uploads through the existing binary cap remain possible by default | Do not confuse raw JSON bytes with base64 characters or decoded file bytes |
| REQ-004 | Error/correlation, request replay, disconnect and SSE/session behavior remain correct | No truncated request delivered to a handler; no mutation on rejection |
| REQ-005 | Configuration and documentation explain both transport and decoded-size limits | No automatic deployment or global concurrency change |

Out of scope: multipart support, streaming native uploads, global caller quotas, production load
benchmarks, dependency upgrades, response field preservation and unknown-argument policy.

## 4. Public contract and technical specification

| Area | Decision |
|---|---|
| Existing tools / routes | All MCP POST traffic under `/mcp` and `/mcp/`; REST POST/PUT/PATCH/DELETE under `/api/v1/` |
| Tool inputs | Existing schemas/defaults remain; no additional tool argument |
| Upload mapping | Existing base64 decode and single `POST uploads.json?filename=...`; no native call for rejected bodies |
| Auth / registration | Existing caller key, write ceiling and catalog; size admission precedes upstream authentication |
| Outputs | Existing success models and receipts; new local HTTP admission errors below |

Add optional positive integer `REDMINE_MAX_REQUEST_BODY_BYTES`. With no override, effective cap is
`max(redmine_max_response_bytes, 4 * ceil(redmine_max_binary_bytes / 3) + 65536)`.
At current defaults the cap is 10 MiB. The 64 KiB allowance covers ordinary filename/JSON/MCP
envelope overhead; it does not promise acceptance of arbitrarily escaped or padded JSON. Explicit
lower caps are allowed and may limit otherwise valid files. Document that setting clearly.

Keep the service's `4 * ceil(max_binary_bytes / 3)` encoded-character check and decoded byte check.
Do not set a fixed schema `maxLength` that disagrees with runtime binary configuration. Existing
maximum-size files represented in ordinary compact JSON must pass with the derived default.

Install the middleware inside request correlation and outside REST read-limit/router and mounted
MCP handling. For relevant requests, reject a declared oversized body immediately. Otherwise read
ASGI messages into bounded storage, check every chunk before retaining it, and replay only a fully
accepted body to the downstream app. Do not truncate and forward. Handler buffering is bounded by
the cap, but ASGI/server input chunks and parser allocations are separate; no absolute process
memory ceiling or concurrent-load guarantee is claimed.

Missing `Content-Length` is valid. Malformed, negative or conflicting duplicate lengths produce a
sanitized 400. Reconcile actual bytes with any valid declared length; mismatch produces 400 unless
actual size already exceeded the cap (413 takes precedence). Any non-identity `Content-Encoding`
produces 415. Do not decode compressed input. A disconnect before completion forwards the
disconnect/terminates processing without invoking a tool. Bodyless GET/SSE and session DELETE
transport behavior remain unchanged. Scope restoration and cancellation must not swallow shutdown.

| Scenario | HTTP status / public error | MCP behavior / retry |
|---|---|---|
| Body exceeds transport cap | 413, `request_body_too_large`, `Request body exceeds the configured limit` | Transport rejection before JSON-RPC parsing; not a fabricated `CallToolResult`; shrink input |
| Invalid/conflicting/mismatched length | 400, `invalid_request_body`, `Invalid request body framing` | Transport rejection; correct framing |
| Non-identity content encoding | 415, `request_encoding_unsupported`, `Encoded request bodies are not supported` | Transport rejection; send plain JSON |
| Accepted envelope, invalid base64 / decoded oversize | Existing 422/413 service behavior | Existing tool-error conversion; zero native upload |
| Accepted envelope, auth/native/transport failure | Existing sanitized behavior | Existing uncertainty rules after dispatch |

New errors include `X-Request-ID` and never echo request bytes, filename, tokens or parser input.
If internal ASGI admission rejects a request, MCPRestClient converts its sanitized envelope as
today. Outer MCP admission errors are ordinary HTTP errors because no JSON-RPC request was parsed.
Accepted writes remain single-attempt; this task introduces no retry or new side effect.
Specification exit: paths, sizes, defaults, framing/error and replay semantics are fixed.

## 5. Implementation plan

| Step | Concrete change | Files/components |
|---|---|---|
| 1 | Add optional setting and effective-cap calculation | `config.py`, `.env.example` |
| 2 | Implement pure ASGI admission, bounded buffering and replay | New `api/body_limits.py`; shared safe errors where appropriate |
| 3 | Place middleware after correlation but before parsers and routers | `app.py`; mounted MCP and internal ASGI path |
| 4 | Retain service encoded/decoded checks; verify configuration agrees | Attachment service/router; no new port/gateway API |
| 5 | Document cap derivation, HTTP MCP rejection and file-size implications | Configuration/tool reference/manual verification/changelog/task/dashboard |
| 6 | Hand off raw-ASGI transport fixtures and tool scenarios | Separately authorized test stage |

No dependency/lockfile or Docker configuration change is planned. Middleware replay must not use
BaseHTTPMiddleware or consume streaming MCP responses. No unsolicited startup or test execution.

## 6. Acceptance criteria and traceability

| Criterion | Given / when | Then |
|---|---|---|
| AC-001 | A declared or actually oversized REST/MCP body arrives | 413 before downstream parsing/auth/native request; buffering stops |
| AC-002 | Missing, chunked, conflicting or wrong framing arrives | Valid unknown lengths are counted; invalid framing cannot bypass admission |
| AC-003 | Compact max-size upload and configured variants are submitted | Encoded/decoded limits and derived body cap agree |
| AC-004 | Accepted request, disconnect, cancellation or MCP streaming occurs | Replay is exact; no double dispatch, hung stream or lost request ID |
| AC-005 | Invalid encoding/configuration or service input is supplied | Documented safe errors and existing writer semantics |

| Requirement | Criterion | Scenario | Evidence / result |
|---|---|---|---|
| REQ-001 | AC-001 | BODY-024-001 | Pending; not run |
| REQ-002 | AC-002 | BODY-024-002 | Pending; not run |
| REQ-003 | AC-003 | BODY-024-003 | Pending; not run |
| REQ-004 | AC-004 | BODY-024-004 | Pending; not run |
| REQ-005 | AC-005 | BODY-024-005/006 | Pending; not run |

## 7. Test plan and execution record

Test implementation, raw-ASGI probes, startup and Inspector are separately authorized work.

| Scenario | Layer / setup | Observable assertion |
|---|---|---|
| BODY-024-001 | Offline raw ASGI, REST and MCP POST | Declared oversize and streamed oversize cause zero parser/SDK/auth/native calls; bounded retained bytes |
| BODY-024-002 | Offline arbitrary ASGI chunks and headers | Missing length, understated length, duplicates, negatives and mismatch have specified results; exact cap and cap+1 |
| BODY-024-003 | Offline normal ASCII base64 at N-1/N/N+1 decoded bytes | Default and custom body/binary caps; no extra native request on rejected content |
| BODY-024-004 | Offline disconnect/cancellation/accepted replay and SDK sessions | Original bytes delivered once; session GET/DELETE and response SSE unchanged; correlation retained |
| BODY-024-005 | Offline encoded body, invalid config/base64 and denied writer | 415/config validation/existing safe errors; no body contents in logs/errors |
| BODY-024-006 | Authorized localhost application and Inspector | Valid ordinary upload through owned writer; oversized MCP HTTP rejection; owned temporary attachment cleanup |

Future Git Bash checks: `bash scripts/check.sh`, assigned unit/integration scenarios, then
authorized startup/Inspector procedures. Raw ASGI cases are necessary because a normal client may
normalize framing. Live native upload parity reuses owned tool-020 fixtures; do not reset shared data.

| Evidence | Procedure | Actual result | Status |
|---|---|---|---|
| EVID-024-001 | Source/configuration inspection on 2026-10-07 | Late limit location identified; no memory benchmark or runtime call | Planning only |
| EVID-024-002 | Offline/startup/Inspector scenarios BODY-024-001..006 | Not run; separate verification assignment required | Pending |
| EVID-024-003 | `bash scripts/doctor.sh` in Git Bash, 2026-10-07 | Required prerequisites ready; Python 3.13.3, uv 0.12.21; no dependencies installed | Passed |
| EVID-024-004 | `uv run --frozen --no-sync ruff check .` | All checks passed | Passed |
| EVID-024-005 | `uv run --frozen --no-sync ruff format --check .` | 262 files already formatted | Passed |
| EVID-024-006 | `uv run --frozen --no-sync mypy src` | Success: no issues found in 122 source files | Passed |
| EVID-024-007 | `git diff --check` and final source/diff inspection | No whitespace errors; expected CRLF-to-LF notices only; source review recorded below | Passed |

## 8. Implementation and review record

Implemented on 2026-10-07 in the explicitly assigned coding-only stage using
`redmine-implement-task`. Baseline working tree was clean. Historical planning evidence above
is preserved; historical native acceptance does not establish this new admission behavior.

- Added optional positive `redmine_max_request_body_bytes` and the effective-cap property in
  `config.py`; omitted configuration derives the specified upload-aware cap. No dependency,
  lockfile or Docker configuration changed.
- Added pure ASGI `api/body_limits.py`. Declared oversize rejects before receiving; actual chunks
  are checked before retention in one byte buffer. Empty chunks do not accumulate message objects.
  A complete accepted payload is replayed once, then the original receive channel remains
  available to disconnect listeners. Premature disconnect terminates without handler dispatch;
  cancellation propagates and no scope state is rewritten.
- Framing accepts absent length and identical repeated decimal lengths, including combined
  identical comma-list headers and leading zeroes. Malformed/negative/conflicting lengths fail
  safely. Decimal-byte comparison rejects arbitrarily long oversized lengths without unsafe
  integer conversion. Completed mismatch returns 400; actual oversize returns 413 first.
  Non-identity encoding returns 415 without decompression. No request content enters errors/logs.
- Wired admission inside correlation and outside read limits/routes/mounted MCP. Installed
  Starlette source confirms middleware insertion/order and that `Request.json()` buffers before
  decoding. Internal MCP ASGI dispatch crosses the same boundary; existing `MCPRestClient`
  already converts sanitized error envelopes, so no adapter change is needed.
- Inspected the existing encoded and decoded attachment checks and bootstrap configuration;
  both service checks remain intact. No fixed schema maximum, gateway/port, operation ID,
  write gate, receipt, retry or success-model change was required.
- Updated `.env.example`, configuration, tool reference, manual verification, changelog and
  dashboard. The optional override is commented so copied configuration retains cap derivation.
- Applied Ruff formatting only to the three changed runtime files, then ran the static commands
  in EVID-024-004..007. No pre-existing static failures were observed. Git Bash was launched
  directly because the command runner's default Bash/WSL path could not start; no PowerShell
  scripts were used. Final source/diff review found no unrelated changes or credential exposure.

No tests, fixtures, test dependencies, runtime probes, builds, startup, Inspector or live calls
were created, changed or executed. No contract deviation is needed. Runtime claims remain
unverified until the following handoff is executed.

## 9. Completion and handoff

- [x] Effective cap and middleware implemented with correct ordering (source inspection).
- [ ] Boundary/framing/replay/error cases have passing named evidence.
- [ ] Existing upload/session/receipt behavior remains accepted.
- [x] Public configuration, error and upload documentation updated.
- [ ] Owned live temporary attachment state and cleanup evidence recorded.
- [x] Static checks passed and final diff/task/dashboard synchronized.

Final status: blocked - **implementation finished; testing pending**. Contract/coding blockers:
none. Outstanding acceptance prerequisite: separately authorized verification, with existing
offline test infrastructure and the owned pinned Redmine 7.0.2 writer environment for live work.

Next action: assign test implementation for BODY-024-001..005 using raw ASGI fixtures plus
REST/MCP integration. Add exact-cap/cap+1, repeated/combined/huge/mismatched lengths, empty chunks,
encoding, bounded retention, zero rejected dispatch, replay, disconnect/cancellation and
GET/SSE/session DELETE coverage. Exercise default/custom binary and body settings, invalid
configuration/base64, existing writer authorization, receipt compatibility and internal MCP error
conversion. Then authorize startup/Inspector and BODY-024-006 with owned tool-020 upload
fixtures; verify native temporary attachment state and cleanup only those owned objects.
Acceptance criteria AC-001..005 and all BODY-024 scenarios remain pending. No build is required
by this code-only change; no deployment or additional task is included in this handoff.
