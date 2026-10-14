# Configuration

## Runtime settings

The application creates its settings when `create_app()` runs. Local execution reads `.env`
relative to the working directory, so start it from the repository root. Process environment
variables override `.env` values. Unrelated dotenv entries are ignored by the runtime settings.

| Variable | Default | Requirements and purpose |
|---|---|---|
| `REDMINE_URL` | Required | HTTP or HTTPS base URL reachable from MCP; no embedded credentials, query, or fragment. A deployment subpath is supported. |
| `REDMINE_WRITE_ENABLED` | `false` | Enables the separate writer runtime. Base Compose forces this false on `mcp-server` and true on the opt-in `mcp-writer` profile. |
| `REDMINE_WRITER_OPERATIONS` | Empty | Comma-separated write operation IDs, or standalone `allowed_all` to permit every registered write operation. Empty permits no mutations. Unknown IDs and mixed `allowed_all` lists prevent writer startup; a read-only runtime ignores the write ceiling. |
| `REDMINE_TIMEOUT_SECONDS` | `20` | Positive finite read/write timeout in seconds; an inactivity timeout, not an end-to-end deadline. |
| `REDMINE_CONNECT_TIMEOUT_SECONDS` | `5` | Positive finite connection timeout in seconds. |
| `REDMINE_POOL_TIMEOUT_SECONDS` | `5` | Positive finite connection-pool acquisition timeout in seconds. |
| `REDMINE_REQUEST_DEADLINE_SECONDS` | `60` | Positive finite deadline for each upstream HTTP read, including every retry, backoff, connection/pool wait and streamed body acquisition/closure. |
| `REDMINE_READ_RETRY_MAX_ATTEMPTS` | `3` | Total GET attempts including the first, from 1 through 5; 1 disables retries. Mutations remain single attempt. |
| `REDMINE_READ_RETRY_BASE_DELAY_SECONDS` | `0.5` | Positive finite exponential backoff base; must not exceed the maximum delay. |
| `REDMINE_READ_RETRY_MAX_DELAY_SECONDS` | `5` | Positive finite delay cap. A valid `Retry-After` above this cap prevents retry rather than shortening the requested wait. |
| `REDMINE_MAX_RESPONSE_BYTES` | `10485760` | Positive limit on accumulated decoded JSON payload bytes per upstream read. |
| `REDMINE_MAX_BINARY_BYTES` | `5242880` (5 MiB) | Positive decoded-byte limit for writer attachment uploads. Direct attachment downloads are disabled. |
| `REDMINE_MAX_REQUEST_BODY_BYTES` | Derived; currently `10485760` (10 MiB) | Optional positive REST/MCP request-body byte cap before parsing and upstream authentication. Omit to derive it; explicit lower caps can limit otherwise valid uploads. Base Compose does not forward this setting. |
| `REDMINE_MAX_CONNECTIONS` | `100` | Positive maximum number of shared upstream connections. |
| `REDMINE_MAX_KEEPALIVE_CONNECTIONS` | `20` | Nonnegative idle connection limit; must not exceed maximum connections. |
| `REDMINE_MAX_CONCURRENT_REQUESTS` | `50` | Positive shared outgoing-request semaphore limit per server process, including authentication, discovery, and writes. |
| `REDMINE_ADMISSION_TIMEOUT_SECONDS` | `30` | Positive finite maximum wait for an upstream permit; exhaustion returns `503 upstream_busy` before dispatch. |
| `REDMINE_MAX_QUERY_PAGES` | `10` | Positive stateless ceiling for matching pages and continuation depth. First pages remain discovery previews. |
| `REDMINE_READ_OPERATION_MAX_REQUESTS` | `30` | Positive aggregate upstream-attempt ceiling for a reader, including nested auth and metadata probes. |
| `REDMINE_READ_OPERATION_DEADLINE_SECONDS` | `90` | Positive finite deadline for a logical read operation, including admission, acquisition and conversion. |
| `REDMINE_READ_OPERATION_MAX_BYTES` | `10485760` | Positive aggregate decoded-response byte ceiling for a logical reader. |
| `REDMINE_MEMBERSHIP_BATCH_MAX_REQUESTS` | `300` | Positive ceiling for every physical request in one membership write batch, including mutations. |
| `REDMINE_MEMBERSHIP_BATCH_MAX_READ_BYTES` | `31457280` | Positive aggregate GET response byte ceiling (30 MiB) for that batch; write responses retain per-response limits. |
| `REDMINE_MEMBERSHIP_BATCH_DEADLINE_SECONDS` | `300` | Positive finite cooperative deadline for one entire membership write batch. |
| `REDMINE_PUBLIC_URL` | Unset | Optional browser-reachable Redmine base URL, including a subpath, for validated attachment links. Empty means use the upstream origin. Credentials, query and fragment are rejected. |
| `LOG_LEVEL` | `INFO` | `DEBUG`, `INFO`, `WARNING`, `ERROR`, or `CRITICAL`, case insensitive. DEBUG enables application diagnostics; restart/recreate the process to apply changes. |

Values in `.env.example` are placeholders and must be replaced for external use. Invalid
required settings prevent application startup. `REDMINE_API_KEY` and `MCP_API_TOKEN` are retired
runtime settings; remove them from existing external environment files. Synthetic Compose
does not load an env file or include these legacy settings.

The internal MCP-to-REST client configures the HTTPX inactivity timeout plus five seconds,
but its in-process ASGI transport does not enforce that setting as a whole-tool timer.
The application's explicit GET, reader, capability and batch deadlines enforce work limits.
Both services in `deploy/compose.yaml` forward the three `REDMINE_READ_RETRY_*` settings from
the selected environment file with the same defaults as local Python. Versioned synthetic
Compose files ignore that env file and use runtime defaults unless their service environment
is explicitly changed. Setting attempts to `1` disables
GET retry for that process; applying configuration to a running deployment is a separate action.

Request-body admission covers POSTs at `/mcp` and under `/mcp/`, and REST
POST/PUT/PATCH/DELETE under `/api/v1/`, including internal MCP-to-REST calls. Without an explicit
`REDMINE_MAX_REQUEST_BODY_BYTES`, the cap is
`max(REDMINE_MAX_RESPONSE_BYTES, 4 * ceil(REDMINE_MAX_BINARY_BYTES / 3) + 65536)`.
The base64 bound plus 64 KiB accommodates ordinary compact upload JSON and MCP envelopes.
Arbitrarily escaped or padded JSON may still exceed that allowance. Decoded attachment bytes
remain independently limited by `REDMINE_MAX_BINARY_BYTES`; the service also checks encoded
base64 length. Omit the optional setting instead of assigning an empty value.

Local Python reads `REDMINE_MAX_REQUEST_BODY_BYTES` from its process environment or `.env`.
Neither MCP service in the current base Compose file forwards this optional setting. Putting
it only in a Compose `--env-file` does not configure the container; the container derives its
cap from the forwarded response and binary limits. A custom container cap requires an explicit
Compose environment override. See [development](development.md) for local execution.

Declared oversized bodies are rejected immediately; otherwise actual received bytes are counted
before JSON/SDK parsing. Missing `Content-Length` and chunked input are supported. Malformed,
negative, conflicting or mismatched lengths return `400 invalid_request_body`; actual oversize
takes precedence over a length mismatch and returns `413 request_body_too_large`. Non-identity
`Content-Encoding` returns `415 request_encoding_unsupported`; compressed input is not decoded.
Errors use a sanitized envelope and include `X-Request-ID`. Outer MCP rejection is an HTTP
transport error before JSON-RPC parsing; internal REST rejection uses the existing MCP tool-error
conversion. Rejected requests do not reach upstream authentication or mutations.

Only a completely accepted body is replayed downstream. Admission stops at the first oversized
chunk and does not retain it; a disconnect during acquisition stops dispatch. Bodyless GET/SSE
and MCP session DELETE behavior are preserved, as are cancellation and response streaming.
The cap bounds retained request payload bytes, not total process memory, ASGI/server chunk
allocations, parser allocations or concurrent load. PREP-024 did not change Compose forwarding.
Its functional acceptance is recorded in the
[preparation regression evidence](testing/evidence/prep-022-026-testing.md), including
REST/SDK body admission, default-size upload and owned Inspector checks. These results do not
establish a total process-memory or production-load guarantee.

Each REST or MCP request must carry `X-Redmine-API-Key: <personal key>`. The server verifies it
through Redmine's `/users/current.json` and sends that same key on the request's upstream calls.
The server does not persist or log the supplied key. See [security guidance](../SECURITY.md).
Repeated key headers, keys over 512 characters, internal whitespace, and non-ASCII/control
characters are rejected with 401. Surrounding whitespace is trimmed. The HTTP pool never sends
shared cookies or a default authorization header to Redmine.

Every HTTP response includes a server-generated `X-Request-ID`. Application logs use the same
identifier for request and upstream events. Logs contain timing and safe status/error metadata;
they exclude caller input and upstream content. GET retry events include only the attempt,
next attempt, delay, native status and an allowlisted failure reason.

Redmine GETs retry connection/read/write transport errors and timeouts, remote protocol errors,
and native HTTP 429, 502, 503 or 504. The default is three total attempts, including the first.
HTTP 500, invalid JSON or declared data, oversized responses, pool/admission saturation,
permission failures and aggregate budget/deadline errors do not retry. The policy covers
identity verification, discovery, metadata, pagination and writer preflight/read-back GETs.
It repeats only the failing GET; MCP-to-REST dispatch, whole tools, batches and mutations
are not replayed. JSON/binary mutations remain single attempt with existing uncertain receipts.

Retry waits use exponential backoff with jitter: by default 0.25..0.5 seconds before the
second attempt and 0.5..1 second before the third. A single valid `Retry-After` integer or
HTTP-date extends the wait when needed. Invalid or repeated header values use backoff.
A header delay above the configured cap, or a wait that cannot fit the remaining deadline,
ends retry with the current mapped error. Each response closes before waiting, releasing
shared capacity; error bodies are never consumed. Every physical attempt and partial decoded
body remains charged to the existing request/byte budget.

The deadline applies separately to identity lookup and each feature HTTP read; it is not a
deadline for an entire MCP invocation or stream. JSON parsing/model conversion occur after the
HTTP acquisition deadline. All attempts share that same deadline; it never resets on retry.
GET acquisition is clipped to the active aggregate budget's remaining time, including
cooperative membership batches. Existing enclosing capability timers can end sooner.
The cutoff uses the budget's absolute monotonic deadline rather than rebuilding it from two
different clock readings. Decoded chunks are charged as they arrive, including a short tail
from an attempt that fails before completing the response.
The payload limit bounds the accumulated decoded body, not total
process memory or transient decompressor/parser allocations. Oversized results fail with
`502 upstream_response_too_large`; request a smaller page or fewer issue expansions when possible.

These per-upstream limits coexist with the aggregate read-operation limits above. REST GET
readers start the aggregate budget before authentication; internal MCP-to-REST dispatch shares
the MCP read tool's budget. MCP transport authentication and logical discovery have independent
budgets; stream/session lifetimes are not aggregate operations. Writers do not receive an
aggregate mutation deadline. Read request/byte exhaustion produces `422 scan_budget_exceeded`;
aggregate deadline exhaustion produces `504 read_operation_timeout`.

Membership write batches use a dedicated policy, separate from the reader defaults: 300
physical requests, 30 MiB of GET response bytes and a 300-second cooperative deadline.
GET retries and backoff share the remaining batch time. Only the GET acquisition timer is
clipped; no whole-batch timer is added around mutations or previously accepted receipts.
Preflight, mutations, permission/target rechecks and read-back share one scope starting at
batch service entry after authentication. No counter resets per item. The writer service in
base Compose forwards the three batch environment settings; its selected env-file values
override defaults. Built-in synthetic services use runtime defaults unless their Compose
environment is changed.
Preflight may reuse project/user proofs within that phase, but each mutation refreshes
permissions and target evidence. There is no outer cancellation timer over mutations.
Deadline exhaustion stops new dispatches and bounded reads, preserving already accepted
receipts. An in-flight mutation may finish after 300 seconds within its existing timeout;
external cancellation still propagates. Large inventories, slow responses or smaller configured
caps can prevent a ten-item batch from completing. PREP-023 functional acceptance, including
the owned ten-item manager fixture, is recorded in the
[preparation regression evidence](testing/evidence/prep-022-026-testing.md); larger inventories
and production-load guarantees remain outside that evidence.
The shared upstream transport also rechecks the active operation deadline after acquiring an
admission permit, before forwarding the request. Expired queued requests fail without dispatch,
leave `redmine_dispatched` false and release the permit. This applies to both direct and proxy
transports and preserves previously accepted membership receipts.

The default aggregate deadline is 90 seconds and includes every admission wait (up to 30 seconds
per attempt), authentication and feature processing. It does not reserve a separate processing
window after admission; individual upstream timeouts remain unchanged. Explicit environment
values, including those in an existing local `.env`, override these defaults.

If synchronous response conversion exhausts that deadline before REST headers are sent, the
pending response is discarded and replaced with the sanitized 504 error. Once headers have
actually been sent, failures terminate the response rather than replacing it.

Upstream connections retain HTTPX environment proxy routing (`HTTP_PROXY`, `HTTPS_PROXY`,
`ALL_PROXY` and `NO_PROXY`, including HTTPX's platform proxy discovery). Direct and proxy
transport pools share the same semaphore. Set proxy variables in the server process environment;
the application settings file does not load arbitrary proxy variables into that environment.
For Docker, explicitly forward the required variables through deployment configuration.
Do not put proxy credentials in logs or verification evidence.

The semaphore owns permits through response closure, including streamed responses. It bounds
simultaneous physical requests, not request rate or user fairness. No per-user quotas, query
tokens, result cache, or persistent query state are kept. Independent workers and the separate
reader/writer deployments each own their limit. Their combined upstream load can exceed one
process's configured limit.

Paginated readers report `pagination_policy` using `ceil(total / requested_limit)`. At offset
zero, a query larger than the page ceiling returns a preview marked `requires_narrowing=true`.
Positive offsets first enforce `offset + limit <= max_query_pages * limit`, then probe the same
filtered collection at offset zero / limit one before fetching the requested page. Oversized
or growing queries return `422 scope_required`. Counts remain upstream queries and may be
expensive even with limit one. Repeated previews and different small queries remain possible.

Attachment content delivery is disabled. The retired content route returns
`403 attachment_download_disabled` before authentication/upstream work, and cached MCP download
calls are rejected. Metadata tools return browser links only; no export files are generated.
Synthetic Compose sets `REDMINE_PUBLIC_URL` to `http://localhost:8001` for 7.0.2 or
`http://localhost:3001` for 6.0.1. Use the actual public origin/subpath externally.
Browser login and Redmine container permissions still apply. The binary byte setting remains
relevant to writer uploads.
Streams close on success and failure. Unsuccessful statuses are mapped without consuming their
error bodies. Settings validation hides input values in exception strings.

Read results report `visibility.scope=requesting_redmine_user`. A field observation reports only
that Redmine omitted a selected field; it cannot identify the reason or detect hidden records.
If a workflow requires complete project data, give each requesting user the necessary Redmine
read permissions and visibility on relevant projects, then verify with that user's key.

## Detailed DEBUG logs

`LOG_LEVEL=DEBUG` enables console text diagnostics for the application. It is the only
logging switch; `INFO` remains the default. Output includes timestamp, level, logger,
`request_id`, and `call_id`, followed by an event name and selected metadata. There is no
application-managed log file or runtime toggle endpoint. The default console handler writes
to stderr, which Docker captures with other container output.

`request_id` correlates an HTTP request with its internal REST and Redmine work and is returned
as `X-Request-ID`. Each MCP tool invocation and discovery request receives a fresh `call_id`,
including calls rejected by the deployment catalog. The original HTTP request is recovered
through the MCP compatibility facade rather than inherited session context. Calls share an
HTTP correlation when applicable but have distinct call IDs; work outside a logical MCP call
uses `call_id=-`. Both contexts are restored after completion, failure, or cancellation.

DEBUG events cover request operations, authentication and deployment gates, capability states,
upstream attempts and admission waits, retries, pagination, read budgets, and write receipts.
`conditional` and `unknown` capability evidence do not guarantee native permission. Request
and response byte fields are counts only. Budget logs summarize operations and exhaustion,
without logging each response chunk. Endpoint templates replace numeric resource IDs with
`{id}`; unrecognized endpoints and operation names use fixed placeholders.

Exception diagnostics contain at most 20 code locations: file basename, function, and line.
They exclude exception messages, source code, locals, raw tracebacks, credentials/hashes,
headers, cookies, raw URLs/query strings, tool arguments, bodies, business text, filenames,
and attachment content. HTTPX, HTTP Core, FastAPI-MCP, and MCP vendor loggers remain at
WARNING; their records reaching the application console retain level/logger/correlation
but use `vendor_diagnostic details_omitted=true` instead of vendor text or tracebacks.

See [development instructions](development.md#debug-logging) for Git Bash activation and
filtering, and the [implementation and verification handoff](plans/debug-logging.md) for
pending acceptance scenarios. Changing the level does not change tool responses or enable
writer access.

## Synthetic environment

Run `bash scripts/dev-up.sh 7.0.2` or `bash scripts/dev-up.sh 6.0.1` from the repository root.
The argument selects the matching Compose file, project, volumes, state and fixed ports.
No environment switches, dotenv file or host state directory are required. Each version's
Compose file is self-contained, with fixed local credentials and internal synthetic markers.
Root `.env` and inherited Compose switches are ignored. Named Docker volumes store the
database, attachments and seed state. New versioned project names keep legacy data separate.

| Variable | Synthetic use |
|---|---|
| `POSTGRES_PASSWORD` | Defined as `redmine-local-development`; database/user are `redmine`. |
| `TEST_USER_PASSWORD` | Defined as `redmine-demo-password` for demo accounts. |
| `REDMINE_SECRET_KEY_BASE` | Fixed local Rails secret defined in each version's Compose file. |
| `REDMINE_TEST_MARKER` | Defined internally as `redmine-mcp-synthetic-v1`; users do not set it. |

Synthetic account keys and manifests remain in the project's `seed_state` Docker volume,
mounted at `/seed-state` in Redmine. Backups use the separate `backup_data` volume.
For Inspector, obtain a personal key privately from Redmine's account page. Fixed development
credentials belong only to these localhost stacks; external deployments use separate settings.

Live E2E selects the same built-in project with `REDMINE_E2E_VERSION=6.0.1` or `7.0.2`.
Pytest automatically adds `deploy/compose.e2e.yaml` and prepares fixture data before executing
`tests/e2e --run-e2e`. The overlay mounts private host state at `.local/e2e/<project>/`;
ordinary development startup uses the named `e2e_state` volume instead. Built-in E2E does
not read an env file or require users to set synthetic markers.

Custom E2E profiles have a separate, explicit env-file contract. Clear previously exported
custom-profile variables before returning to the built-in defaults; see
[test profile configuration](testing-roadmap.md#selecting-a-redmine-release). The lifecycle
helper selector `REDMINE_TEST_VERSION` and test selector `REDMINE_E2E_VERSION` have different
entry points; the E2E launcher aligns them internally.

## Local and Docker addresses

| Caller | Redmine address |
|---|---|
| Local Python process using synthetic Redmine 7.0.2 / 6.0.1 | `http://localhost:8001` / `http://localhost:3001` |
| MCP container with the synthetic Compose override | `http://redmine:3000` |
| Container accessing Redmine on the Windows host | Use `http://host.docker.internal:<port>` with the actual port. |

Base Compose for external deployments passes runtime settings from its interpolation environment.
The standalone synthetic files explicitly set `REDMINE_URL` to the container service URL.
Direct Docker Compose commands allow shell variables to override `--env-file`.
The synthetic helpers isolate Compose interpolation from inherited shell settings.

Published synthetic endpoints bind to localhost: 7.0.2 uses MCP `8000`, Redmine `8001`,
PostgreSQL `5433`; 6.0.1 uses `8002`, `3001`, `5436`. These ports are fixed in the versioned
Compose files; occupied ports cause startup to stop with a diagnostic. Base Compose for
external Redmine still supports `MCP_HOST_PORT`. MCP listens on container port `8000`.
PostgreSQL uses port `5432` inside Docker. MCP never connects to PostgreSQL.
Stop the MCP container before starting local Python on port `8000`.

## External Redmine

Create a separate ignored configuration file:

```bash
mkdir -p .local
cp -n .env.example .local/external.env
```

Edit `.local/external.env` privately and set the actual Redmine URL. Base Compose needs only
runtime settings; synthetic database/account values do not
configure external Redmine. Start MCP using the [operations guide](operations.md).

Do not run seed, reset, or restore against an external instance. Do not disable TLS verification.
Do not share `docker compose config` output because interpolation can expose secrets.

## Separate writer deployment

Base Compose keeps `mcp-server` read-only. The opt-in `mcp-writer` profile binds to
localhost port `8001` by default (`MCP_WRITER_HOST_PORT`). Prepare a separate ignored env-file:

```bash
mkdir -p .local
cp -n .env.example .local/writer.env
chmod 600 .local/writer.env
```

Choose an unused writer port. The built-in 7.0.2 Redmine already uses host port `8001`, so
set `MCP_WRITER_HOST_PORT=8010` in this separate writer env-file when connecting to that stack.
Built-in synthetic Compose files instead define optional writer ports `8004` for 7.0.2 and
`8003` for 6.0.1. Those writers are not started by `dev-up.sh` and have an empty operation
ceiling until their service environment is explicitly configured. They do not load this env-file.

Edit it privately to set the reachable `REDMINE_URL`, `REDMINE_WRITE_ENABLED=true`, and
the intended `REDMINE_WRITER_OPERATIONS`. An empty operation list permits no mutations;
standalone `allowed_all` permits all registered writes, including future additions.
These settings belong to the writer env-file. Compose forces the writer gate true;
a local writer needs the explicit setting.

Every caller supplies their own `X-Redmine-API-Key`. Authentication verifies the key through
Redmine, and all upstream calls use that same key. Any authenticated caller can attempt the
configured writes; native target permissions still decide access. The server has no key hash
or user ID admission list. Use ordinary users with the needed project roles and restrict access
to the listener and env-file.

`REDMINE_WRITER_AUTH_MODE`, `REDMINE_WRITER_USER_IDS`, and `REDMINE_WRITER_KEY_SHA256`
are retired and ignored. Remove them from existing private environment files to avoid confusion.
Restart the local process or recreate the writer container to load the new code and settings,
then reconnect clients. Do not roll back to a pinned-key configuration on this version.

All MCP HTTP requests reauthenticate. Stateful sessions bind to user ID, configured Redmine
issuer and a private key fingerprint through MCP SDK 1.30.0. A different user/key receives the
same 404 as an unknown session; key rotation requires a new session. Session binding is removed
on termination, expiry and shutdown. Keys/fingerprints are never returned or logged.

Writes also read the caller's project memberships and role permissions through
`users/current.json?include=memberships` and `roles/{id}.json`. The internal capability snapshot
is request-local and checks the actual project/resource context before dispatch. A known absent
necessary permission is denied with 403. A present permission is conditional; tracker, workflow,
field, ownership, visibility and project/module rules remain enforced by Redmine. Missing
membership or inaccessible role metadata is unknown evidence and never proves denial or a grant.
Malformed metadata, timeout or transport failure stops dispatch with a sanitized upstream error.
No role-name mapping, administrator substitution or cross-request permission cache is used.

Writer MCP discovery returns a caller-specific candidate list. It retains all read tools,
applies configured operations, and hides only writes proved unavailable across the caller's
completely inventoried visible projects. A project without
membership or role metadata keeps evidence unknown, so potentially usable tools remain visible.
Visible projects are inventoried in pages of 100, capped by `REDMINE_MAX_QUERY_PAGES` and the
aggregate read budget. Oversized inventories remain incomplete; partial/changing evidence
cannot prove denial. Role definitions are deduplicated only within this discovery request.

Tool availability does not guarantee permission for a concrete target. Every direct or cached
tool call still passes REST deployment and resource authorization. A fresh `tools/list` refreshes
evidence; no proactive list-change notification is promised. The MCP adapter returns copied
definitions and never mutates the shared superset schema cache for another caller.

The writer catalog contains only configured operation IDs from the code's explicit write allowlist.

To permit every registered write operation without listing individual names, use:

```bash
REDMINE_WRITER_OPERATIONS=allowed_all
```

The lowercase `allowed_all` value must be used alone; surrounding whitespace is ignored.
It expands to the code's complete `WRITE_OPERATIONS` catalog for MCP discovery, REST admission
and project capability reporting, including membership writes. New registered write operations
are also permitted after upgrading the server. Use an explicit CSV list to keep a fixed scope.
This option still requires `REDMINE_WRITE_ENABLED=true` on the separate writer deployment;
caller permissions and native Redmine authorization still apply.
Recreate the Compose writer after changing its env-file using the
[startup command](operations.md#separate-writer), or restart a local writer process with the
new environment; a plain Compose restart retains the existing container environment.
Refresh client connections and tool lists.

To permit project membership writes, explicitly configure only the needed operations in the
separate ignored writer env-file, for example:

```bash
REDMINE_WRITER_OPERATIONS=add_project_members,update_project_members,delete_project_members
```

Retain `REDMINE_WRITE_ENABLED` and authenticate each caller with their personal API key.
Grant an ordinary caller `manage_members` in each destination project. Role-management limits
remain native Redmine constraints; this permission does not authorize every role change.
Membership listing requires no writer setting. Redmine 7.0.2 public `view_members` still checks
project access. These examples do not modify deployed configuration or enable mutations.
See [membership contracts](tool-reference.md#project-membership-management).

To permit Target version creation, explicitly include `create_project_version` in the separate
ignored writer env-file's operation list. A writer limited to that mutation uses:

```bash
REDMINE_WRITER_OPERATIONS=create_project_version
```

Retain the writer's existing authentication settings and write gate. Grant the ordinary caller
`manage_versions` in each destination project. `view_issues` is needed only for version read-back
and duplicate recovery; creation does not require it. See the [tool contract](tool-reference.md#create-project-version).
This example does not change deployed configuration or enable writes on the reader.

An empty `REDMINE_WRITER_OPERATIONS` exposes no write tools or REST mutations; unknown IDs prevent
startup. Every write route uses `require_write_access`, which checks its operation ID
against the expanded configured list. Reader REST write attempts return 403. No public write
operation is admitted on the reader. The current explicit catalog has 18 write operations;
see the [tool reference](tool-reference.md) for each native permission and outcome contract.

`create_time_entry` requires the same separate writer gates, a visible issue and native
`log_time` in its resolved project. Add that ID to a fixed CSV allowlist, or keep standalone
`allowed_all` to include it after upgrading/restarting the writer. Supply an explicit spent_on
date; optional activity uses the native caller/project default. Time-entry read permission is
only needed for discovery/read-back. This documentation does not alter deployed configuration;
TOOL-041 runtime acceptance remains pending.

`update_time_entry` uses the same writer gates at
`PUT /api/v1/issues/{issue_id}/time-entries/{time_entry_id}`. Add its operation ID to a fixed
CSV allowlist or retain standalone `allowed_all` after upgrading/restarting the writer.
The caller needs a visible issue and entry, native `view_time_entries`, and `edit_time_entries`
or `edit_own_time_entries` when the entry is credited to that caller. `log_time` alone does
not authorize editing. Only supplied hours/date/activity/comments change; issue/project/user
reassignment is excluded. [TOOL-042 acceptance](testing/evidence/tool-042-testing.md) records
owned native state/permissions, offline cases, Inspector and exact cleanup. Alternative global
policy settings remain unforced variants. No deployed configuration was changed.

`delete_time_entry` uses the same separate writer/caller gates at
`DELETE /api/v1/issues/{issue_id}/time-entries/{time_entry_id}`. Add this operation ID to a fixed
CSV allowlist or retain standalone `allowed_all` after upgrading/restarting the writer.
The caller needs issue and entry visibility, `view_time_entries`, and `edit_time_entries` or
eligible `edit_own_time_entries` based on the credited user. `log_time` alone is insufficient.
Each call permanently removes one entry without undo; accepted/uncertain receipts remain separate
from later caller-visible presence. GET 404 cannot prove an uncertain DELETE committed.
[TOOL-043 acceptance](testing/evidence/tool-043-testing.md) records offline/native/Inspector
verification, exact owned cleanup and fault/policy limits. No deployed configuration was changed.

The write transport sends each mutation once, bounds JSON and binary requests and JSON responses,
validates each operation's native success status/body, and returns an `uncertain` receipt when a
request may have reached Redmine but a reliable response could not be obtained. Callers must
inspect uncertain results before trying again. Logs record method, status, and timing without
the request body, key, or response content. Selected native state/permission acceptance is in
the [2026-10-07 ledger](testing/evidence/current-catalog-acceptance.md); broader historical variants and
operational readiness remain open. Configuration alone does not establish acceptance.

Every JSON and binary mutation classifies a received HTTP 500-599 as `uncertain`. There is no
per-operation opt-in or configuration switch. Individual results retain `outcome=uncertain`
and `upstream_accepted=null`; create/upload results do not invent a new resource ID or token.
Known target IDs remain available for reconciliation. Existing known-target read-back can
report observations independently, but cannot turn uncertainty into confirmed acceptance.
No server-error response body is parsed or exposed, and the response is closed.

Authentication, preflight, and read-back GETs retain their existing sanitized read errors.
A failed initial preflight dispatches no mutations; failed read-back preserves the preceding
mutation receipt. No automatic retry or rollback is added. Received-5xx behavior changes callers'
error handling: inspect the returned receipt before deciding whether to attempt the write again.

Membership update/delete additionally accept native 200 or 204, including empty success bodies.
Membership batches retain `phase` and per-item `results`. A mutation 5xx leaves `phase=executed`
and the dispatched item's `outcome=uncertain`, `verification=unavailable`, and
`error.code=write_outcome_uncertain`. It returns without read-back, preserves accepted peers,
and leaves later items `not_executed`. No batch-wide acceptance field is added. Acceptance and
actual read-back state are reported independently; interrupted response delivery requires
manual reconciliation. Prep-019 acceptance passes offline and in the owned Redmine 7.0.2
commit/HTTP-500 reconciliation scenario; Inspector discovery/schema compatibility also passes.
