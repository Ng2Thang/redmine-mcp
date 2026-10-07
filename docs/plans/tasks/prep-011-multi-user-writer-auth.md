# prep-011-multi-user-writer-auth: Authenticate multiple personal writer keys

## 1. Task identity and status

| Field | Value |
|---|---|
| Task ID | prep-011-multi-user-writer-auth |
| Assigned capability | Users read and attempt enabled writes using their own Redmine keys |
| Type / access / destructive effects | Shared authentication prerequisite / mixed read-write access / Existing writes only |
| Status | blocked |
| Dependencies | [prep-010](prep-010-permission-session-contract.md) contract resolved; existing prep-007 implementation |
| Related tasks | [Roadmap](../multi-user-writer-authorization.md); [dashboard](../index.md); [prep-014](prep-014-multi-user-writer-acceptance.md) |
| Target Redmine version | 7.0.2; runtime acceptance pending |
| Last updated | 2026-10-05, Codex |
| Progress summary | Personal/pinned modes, write-only admission, same-key forwarding and SDK session binding implemented; static checks pass |
| Next action | Continue assigned prep-012 coding; execute AUTH scenarios separately in prep-014 |

## 2. Discovery and evidence

Current writer authentication rejects a nonmatching hash before upstream identity lookup, then
checks configured user IDs. This applies even to reads and MCP connection. `bootstrap.py` and
`RedmineWriter` already pass the request's personal key upstream.
Sources checked 2026-10-05: `config.py`, `api/security.py`, `auth/*`, `bootstrap.py`,
`integrations/redmine/identity.py`, `mcp/registration.py`, and `deploy/compose.yaml`.
The [Users API](https://www.redmine.org/projects/redmine/wiki/Rest_Users) identifies the caller;
exact source evidence and verified 7.0.2 archive are in the [roadmap](../multi-user-writer-authorization.md).
No target runtime verification establishes account/key variants yet. Working tree initially clean.

Decision: keep legacy pinned-key mode as default and explicitly select personal-key mode.
No new MCP tool, bearer token, OAuth flow, shared writer credential, or user-supplied identity field.

## 3. Requirements

| ID | Required observable behavior |
|---|---|
| REQ-001 | Two ordinary users with distinct valid keys authenticate independently in personal-key mode |
| REQ-002 | Writer admission controls writes without blocking valid users' reads/connections in personal-key mode |
| REQ-003 | Reader writes remain disabled and pinned-key behavior remains compatible by default |
| REQ-004 | Requests, concurrent calls, and session reuse cannot switch caller or upstream key |
| REQ-005 | Invalid and contradictory configuration fails safely before startup completes |

Synthetic example: user 101 and user 102 use separate keys. With empty writer user IDs both may
attempt enabled writes; Redmine can permit 101 in project A and deny 102 there. With user IDs
`101`, user 102 can read/connect but cannot write. No real IDs/keys are stored in documentation.

## 4. Public contract and technical specification

### Interface and configuration

Existing operation IDs, REST paths, tool arguments, and response schemas are preserved.
The phase uses the common deployment catalog; caller filtering belongs to prep-013.

| Input | Type / default | Validation and mapping |
|---|---|---|
| `X-Redmine-API-Key` | One required header | Existing normalization; authenticate upstream; keep key private in AuthContext |
| `REDMINE_WRITE_ENABLED` | Boolean / false | Existing reader/writer boundary retained |
| `REDMINE_WRITER_AUTH_MODE` | `pinned_key` or `personal_key` / `pinned_key` | Unknown values fail settings validation |
| `REDMINE_WRITER_KEY_SHA256` | String / empty | Existing digest required in enabled pinned-key mode; must be empty in personal-key mode |
| `REDMINE_WRITER_USER_IDS` | CSV positive IDs / empty | Pinned-key mode retains required allowlist; personal-key empty permits any authenticated caller to attempt writes; malformed lists fail startup |
| `REDMINE_WRITER_OPERATIONS` | Existing operation CSV / empty | Unknown operations fail startup; empty exposes/allows no writes |

Pinned-key mode preserves the current common-auth key/user checks. Personal-key mode authenticates
every valid caller via `GET /users/current.json`; optional user admission is applied only by the
write gate. Every enabled write still passes the deployment operation check. All upstream calls
use the normalized key received for that request. Authentication success is not write permission.

Session binding follows prep-010's reviewed adapter design. Bind to user ID plus a private
credential fingerprint; changed key/user requires a new session. Authenticate each POST/GET/DELETE
request before accessing session state. Reject mismatched caller with SDK 404 and do not dispatch any
tool or expose session data. Preserve normal SDK behavior for an unknown session ID. Remove binding
on session termination and lifespan shutdown. No process-global mutable current-user variable.

Request-local identity reuse is allowed; cross-request positive auth caching is excluded.
Upstream current-user response fields, including echoed API key, are not returned by auth.

### Errors and write semantics

| Scenario | REST boundary | MCP behavior / dispatch |
|---|---|---|
| Missing, duplicate, malformed, or rejected key | Existing sanitized 401 | Connection rejected; no tool dispatch |
| Authenticated caller outside write admission or disabled operation | Existing sanitized 403 | Tool error through existing adapter; no mutation |
| Session caller/key mismatch | 404 | SDK responds as for an unknown session before session access |
| Missing/hidden resource, field validation, upstream permission | Existing operation error contract | Redmine remains authoritative using caller key |
| Identity timeout/transport failure/malformed response | Existing upstream 504/503/502 mapping | Fail authentication; do not use stale principal |
| Invalid settings | Startup validation failure with secret-safe message | No ready MCP service |

Success responses, pagination, and resource error mappings remain owned by existing tools.
Existing writes can create/update/delete resources with no rollback promise. Preserve bounded
single-attempt transport, accepted versus uncertain outcomes, independent read-back, and cleanup
rules in tool-020 through tool-030. Authentication failures happen before mutation.

Specification exit: product behavior and the [prep-010 session integration](../../reviews/prep-010-contract-review.md)
are resolved. Adapt authenticated scope to SDK owner binding; no exact permission list or dynamic
discovery is promised by this phase.

## 5. Implementation plan

| Step | Changes and ownership | Verification handoff |
|---|---|---|
| 1 | `config.py`, runtime/auth constants: explicit mode and validation | AUTH-001/002 |
| 2 | `api/security.py`, auth wiring: separate authentication from personal-mode write admission | AUTH-003/004 |
| 3 | MCP registration/transport adapter: bind sessions according to prep-010; preserve forwarding | AUTH-005/006 |
| 4 | `deploy/compose.yaml`, tracked env examples: pass mode and safe empty defaults; reader remains disabled | AUTH-007 |
| 5 | Architecture/config/tool-reference/manual guides and changelog: migration and rollback | AUTH-008 |
| 6 | Coding assignment runs `bash scripts/check.sh`; testing fixtures/execution handed off to prep-014 | Static checks only during coding |

No new runtime package added. MCP SDK metadata is pinned to the already locked 1.30.0 because
session security depends on its reviewed owner binding; uv.lock resolved offline without upgrades.
Rollback selects pinned-key mode with its valid hash/user configuration and reconnects clients.

## 6. Acceptance criteria and traceability

| Criterion | Requirement | Observable result | Scenarios |
|---|---|---|---|
| AC-001 | REQ-001 | Distinct keys resolve correct users and are forwarded unchanged | AUTH-003/005 |
| AC-002 | REQ-002 | Admission denies writes only; valid caller still reads/connects | AUTH-004 |
| AC-003 | REQ-003 | Default pinned mode and reader isolation retain prior behavior | AUTH-001/007/008 |
| AC-004 | REQ-004 | Concurrent callers, stolen session ID, rotation, shutdown remain isolated | AUTH-005/006 |
| AC-005 | REQ-005 | Invalid mode/hash/IDs/operations fail before readiness | AUTH-002 |

All acceptance results pending; source inspection is not runtime acceptance.

## 7. Test plan and execution record

Tests are planned only. Reuse prep-002's fake settings, MockTransport, ASGI lifespan and MCP SDK.
No real credentials, Docker, or `.env` in offline scenarios.

| Scenario | Setup and expected result | Mode |
|---|---|---|
| AUTH-001 | Omitted mode keeps pinned-key checks; nonmatching key denied | Offline |
| AUTH-002 | Invalid mode/ID CSV/operation and contradictory personal-mode hash fail startup | Offline |
| AUTH-003 | Two valid keys, revoked/locked key, duplicate header, malformed identity | Offline; synthetic account variants later |
| AUTH-004 | Empty admission and restricted list; excluded caller reads but write never dispatches | REST/MCP offline |
| AUTH-005 | Concurrent callers and upstream captures always match each request key | Offline MCP |
| AUTH-006 | Existing session with another user/key rejected, including GET/DELETE; cleanup/rotation | Offline MCP; opt-in Inspector |
| AUTH-007 | Reader omits/denies every write; personal writer common catalog matches configured ceiling | Offline REST/MCP |
| AUTH-008 | Documented personal-mode migration and pinned-mode rollback | Document review; opt-in startup |

| Evidence | Procedure | Actual / status |
|---|---|---|
| EVID-001 | Installed Ruff check/format, mypy src, and git diff --check; 2026-10-05 | Pass; unit/startup/live checks deferred |
| EVID-002 | Separately authorized selected AUTH scenarios via existing pytest baseline | Not run / pending |
| EVID-003 | Separately authorized synthetic startup/Inspector and account checks | Not run / pending |

## 8. Implementation and review record

Implemented on 2026-10-05: explicit writer mode and validation, write-only optional personal-mode
admission, legacy pinned behavior, per-request SDK session identity, Compose and environment
examples, migration/rollback, architecture/manual/tool documentation and changelog.
MCP metadata pinned to already installed 1.30.0; `uv lock --offline` changed only the root
requirement, with no package upgrades. `scripts/doctor.sh` passed through Git Bash.
Installed Ruff lint and formatting checks pass repository-wide; mypy src passes (100 files);
git diff --check passes. Formatting applied only to changed security.py.
No tests/fixtures written or run in this coding stage; AUTH-001 through AUTH-008 and packaging
verification for the metadata change remain assigned to prep-014. SDK-native 404 session mismatch
was resolved by prep-010. Final diff preserves all existing tool contracts and secret-safe key use.

## 9. Completion and handoff

- [x] Mode/configuration and multi-user authentication implemented.
- [x] Session binding and exact caller-key forwarding implemented.
- [x] Migration/rollback and deployment documentation updated.
- [ ] Static checks and separately authorized acceptance evidence pass.
- [ ] Task/dashboard synchronized and final diff reviewed.

Final status: blocked - implementation finished; testing pending. Next action: continue the
explicitly assigned prep-012 coding stage; AUTH verification and packaging belong to prep-014.
