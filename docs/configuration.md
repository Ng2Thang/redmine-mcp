# Configuration

## Runtime settings

The application creates its settings when `create_app()` runs. Local execution reads `.env`
relative to the working directory, so start it from the repository root. Process environment
variables override `.env` values. Unrelated dotenv entries are ignored by the runtime settings.

| Variable | Default | Requirements and purpose |
|---|---|---|
| `REDMINE_URL` | Required | HTTP or HTTPS base URL reachable from MCP; no embedded credentials, query, or fragment. A deployment subpath is supported. |
| `REDMINE_WRITE_ENABLED` | `false` | Enables the separate writer runtime. Base Compose forces this false on `mcp-server` and true on the opt-in `mcp-writer` profile. |
| `REDMINE_WRITER_AUTH_MODE` | `pinned_key` | `pinned_key` accepts one configured key; explicit `personal_key` authenticates each caller's own Redmine key. |
| `REDMINE_WRITER_USER_IDS` | Empty | Positive user ID CSV. Required in enabled pinned-key mode; optional write-only admission list in personal-key mode. Empty personal-key list admits any authenticated caller to attempt enabled writes. |
| `REDMINE_WRITER_OPERATIONS` | Empty | Comma-separated write operation IDs, or standalone `allowed_all` to permit every registered write operation. Empty permits no mutations. Unknown IDs and mixed `allowed_all` lists prevent startup. |
| `REDMINE_WRITER_KEY_SHA256` | Empty | Private lowercase SHA-256 digest required for enabled pinned-key mode. Must be empty in personal-key mode; conflicting settings prevent startup. |
| `REDMINE_TIMEOUT_SECONDS` | `20` | Positive finite read/write timeout in seconds; an inactivity timeout, not an end-to-end deadline. |
| `REDMINE_CONNECT_TIMEOUT_SECONDS` | `5` | Positive finite connection timeout in seconds. |
| `REDMINE_POOL_TIMEOUT_SECONDS` | `5` | Positive finite connection-pool acquisition timeout in seconds. |
| `REDMINE_REQUEST_DEADLINE_SECONDS` | `60` | Positive finite deadline for each upstream HTTP read, including connection/pool waits and streamed body acquisition/closure. |
| `REDMINE_MAX_RESPONSE_BYTES` | `10485760` | Positive limit on accumulated decoded JSON payload bytes per upstream read. |
| `REDMINE_MAX_BINARY_BYTES` | `5242880` (5 MiB) | Positive decoded-byte limit for writer attachment uploads. Direct attachment downloads are disabled. |
| `REDMINE_MAX_CONNECTIONS` | `100` | Positive maximum number of shared upstream connections. |
| `REDMINE_MAX_KEEPALIVE_CONNECTIONS` | `20` | Nonnegative idle connection limit; must not exceed maximum connections. |
| `REDMINE_MAX_CONCURRENT_REQUESTS` | `50` | Positive shared outgoing-request semaphore limit per server process, including authentication, discovery, and writes. |
| `REDMINE_ADMISSION_TIMEOUT_SECONDS` | `30` | Positive finite maximum wait for an upstream permit; exhaustion returns `503 upstream_busy` before dispatch. |
| `REDMINE_MAX_QUERY_PAGES` | `10` | Positive stateless ceiling for matching pages and continuation depth. First pages remain discovery previews. |
| `REDMINE_READ_OPERATION_MAX_REQUESTS` | `30` | Positive aggregate upstream-attempt ceiling for a reader, including nested auth and metadata probes. |
| `REDMINE_READ_OPERATION_DEADLINE_SECONDS` | `90` | Positive finite deadline for a logical read operation, including admission, acquisition and conversion. |
| `REDMINE_READ_OPERATION_MAX_BYTES` | `10485760` | Positive aggregate decoded-response byte ceiling for a logical reader. |
| `REDMINE_PUBLIC_URL` | Unset | Optional browser-reachable Redmine base URL, including a subpath, for validated attachment links. Empty means use the upstream origin. Credentials, query and fragment are rejected. |
| `LOG_LEVEL` | `INFO` | `DEBUG`, `INFO`, `WARNING`, `ERROR`, or `CRITICAL`, case insensitive. |

Values in `.env.example` are placeholders and must be replaced for external use. Invalid
required settings prevent application startup. `REDMINE_API_KEY` and `MCP_API_TOKEN` are retired
runtime settings; remove them from existing external environment files. The synthetic setup
helper removes them from its marked `.env`.
The internal MCP-to-REST client uses the configured timeout plus five seconds.

Each REST or MCP request must carry `X-Redmine-API-Key: <personal key>`. The server verifies it
through Redmine's `/users/current.json` and sends that same key on the request's upstream calls.
The server does not persist or log the supplied key. See [security guidance](../SECURITY.md).
Repeated key headers, keys over 512 characters, internal whitespace, and non-ASCII/control
characters are rejected with 401. Surrounding whitespace is trimmed. The HTTP pool never sends
shared cookies or a default authorization header to Redmine.

Every HTTP response includes a server-generated `X-Request-ID`. Application logs use the same
identifier for request and upstream events. Logs contain timing and safe status/error metadata;
they exclude caller input and upstream content. No automatic upstream retries are performed.

The deadline applies separately to identity lookup and each feature HTTP read; it is not a
deadline for an entire MCP invocation or stream. JSON parsing/model conversion occur after the
HTTP acquisition deadline. The payload limit bounds the accumulated decoded body, not total
process memory or transient decompressor/parser allocations. Oversized results fail with
`502 upstream_response_too_large`; request a smaller page or fewer issue expansions when possible.

These per-upstream limits coexist with the aggregate read-operation limits above. REST GET
readers start the aggregate budget before authentication; internal MCP-to-REST dispatch shares
the MCP read tool's budget. MCP transport authentication and logical discovery have independent
budgets; stream/session lifetimes are not aggregate operations. Writers do not receive an
aggregate mutation deadline. Read request/byte exhaustion produces `422 scan_budget_exceeded`;
aggregate deadline exhaustion produces `504 read_operation_timeout`.

Membership write batches also use one shared read budget for preflight, permission/target
rechecks and read-back. The budget starts at batch service entry after authentication; it does
not install an outer cancellation timer over mutations. Deadline exhaustion is checked by
bounded reads and before dispatch, preserving already accepted receipts. Each mutation retains
its single-attempt upstream timeout. Smaller batches may be needed to fit the read budget.
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
For the synthetic Docker deployment, configure `REDMINE_PUBLIC_URL=http://localhost:3000` when
the browser runs on the same Windows host. Use the actual public origin/subpath externally.
Browser login and Redmine container permissions still apply. The binary byte setting remains
relevant to writer uploads.
Streams close on success and failure. Unsuccessful statuses are mapped without consuming their
error bodies. Settings validation hides input values in exception strings.

Read results report `visibility.scope=requesting_redmine_user`. A field observation reports only
that Redmine omitted a selected field; it cannot identify the reason or detect hidden records.
If a workflow requires complete project data, give each requesting user the necessary Redmine
read permissions and visibility on relevant projects, then verify with that user's key.

## Synthetic environment

Run `bash scripts/dev-up.sh` from the repository root. It generates `.env` with random secrets
when absent. Do not copy `.env.example` for this workflow. Existing configuration must carry
the synthetic marker; keep real-instance configuration separate.

| Variable | Synthetic use |
|---|---|
| `POSTGRES_PASSWORD` | Generated database password; database and user are both `redmine`. |
| `TEST_USER_PASSWORD` | Generated password for the synthetic Redmine accounts. |
| `REDMINE_SECRET_KEY_BASE` | Generated Rails secret, passed as both `REDMINE_SECRET_KEY_BASE` and `SECRET_KEY_BASE` in the Redmine container. |
| `REDMINE_TEST_MARKER` | Must be `redmine-mcp-synthetic-v1`; checked alongside local state before destructive operations. |

Synthetic account keys used for seeding remain in ignored `.local/credentials.json`. The setup
does not put a Redmine API key in `.env`. For Inspector, obtain a personal key privately from
Redmine's account page or the synthetic credentials file. Generated state, credentials,
manifests, and backups live in ignored `.local/`.

## Local and Docker addresses

| Caller | Redmine address |
|---|---|
| Local Python process using the synthetic environment | `http://localhost:3000` |
| MCP container with the synthetic Compose override | `http://redmine:3000` |
| Container accessing Redmine on the Windows host | Use `http://host.docker.internal:<port>` with the actual port. |

Base Compose passes the runtime settings from its interpolation environment into MCP.
The synthetic override explicitly replaces `REDMINE_URL` with the container service URL.
Compose shell variables can override values from `--env-file`; avoid stale exported credentials.

Published endpoints bind to localhost: MCP defaults to `8000` (Compose `MCP_HOST_PORT`),
Redmine `3000`, PostgreSQL `5433`. `MCP_HOST_PORT` configures only the published Compose port;
the application still listens on container port `8000`.
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

Base Compose always keeps `mcp-server` read-only. The opt-in `mcp-writer` profile binds to
localhost port `8001` by default (`MCP_WRITER_HOST_PORT`). It needs a separate ignored env-file
with explicit authentication mode. Default `pinned_key` requires `REDMINE_WRITER_USER_IDS` and
`REDMINE_WRITER_KEY_SHA256`. Generate the digest locally in Git
Bash without putting the personal key in a command argument or history:

```bash
read -rs writer_key; printf '\n'
printf '%s' "$writer_key" | sha256sum | cut -d ' ' -f 1
unset writer_key
```

Copy the digest into the ignored writer env-file. Use a dedicated ordinary Redmine user with only
the needed project roles and personal key; never use an administrator key. Restrict access to the
writer listener and env-file. The writer compares the key digest before calling Redmine, then
checks the returned Redmine user ID. A different key receives 401, and a mismatched user receives
403. Both REST and MCP requests use this boundary. The writer still exposes existing read tools
to its restricted caller.

For multiple callers, configure the separate ignored writer env-file with:

```bash
REDMINE_WRITER_AUTH_MODE=personal_key
REDMINE_WRITER_KEY_SHA256=
REDMINE_WRITER_USER_IDS=
```

Each caller supplies their own `X-Redmine-API-Key`; authentication resolves the caller through
Redmine and every upstream call uses that key. An optional user ID list restricts writes only;
valid excluded users still read and connect. Empty user IDs do not grant Redmine permissions.
The configured operation list and upstream permissions remain required. No shared administrator
key or impersonation is used. Roll back by selecting `pinned_key`, supplying its valid digest
and user IDs, and reconnecting clients.

All MCP HTTP requests reauthenticate. Stateful sessions bind to user ID, configured Redmine
issuer and a private key fingerprint through MCP SDK 1.30.0. A different user/key receives the
same 404 as an unknown session; key rotation requires a new session. Session binding is removed
on termination, expiry and shutdown. Keys/fingerprints are never returned or logged.

Personal-key writes also read the caller's project memberships and role permissions through
`users/current.json?include=memberships` and `roles/{id}.json`. The internal capability snapshot
is request-local and checks the actual project/resource context before dispatch. A known absent
necessary permission is denied with 403. A present permission is conditional; tracker, workflow,
field, ownership, visibility and project/module rules remain enforced by Redmine. Missing
membership or inaccessible role metadata is unknown evidence and never proves denial or a grant.
Malformed metadata, timeout or transport failure stops dispatch with a sanitized upstream error.
No role-name mapping, administrator substitution or cross-request permission cache is used.

Personal-key MCP discovery returns a caller-specific candidate list. It retains all read tools,
applies the optional write admission list and configured operations, and hides only writes proved
unavailable across the caller's completely inventoried visible projects. A project without
membership or role metadata keeps evidence unknown, so potentially usable tools remain visible.
Visible projects are inventoried in pages of 100, capped by `REDMINE_MAX_QUERY_PAGES` and the
aggregate read budget. Oversized inventories remain incomplete; partial/changing evidence
cannot prove denial. Role definitions are deduplicated
only within this discovery request. Default pinned-key discovery keeps its common catalog.

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
writer identity restrictions, caller permissions and native Redmine authorization still apply.
Restart the writer after changing its environment and refresh the MCP connection's tool list.

To permit project membership writes, explicitly configure only the needed operations in the
separate ignored writer env-file, for example:

```bash
REDMINE_WRITER_OPERATIONS=add_project_members,update_project_members,delete_project_members
```

Retain `REDMINE_WRITE_ENABLED`, pinned/personal-key authentication and user restrictions.
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
startup. Each future write route must use `require_write_access`, which checks its operation ID
against the expanded configured list. Reader REST write attempts return 403. No public write
operation is part of this prerequisite.

The write transport sends each mutation once, bounds JSON and binary requests and JSON responses,
accepts 201 with a JSON object or 204 without a body, and returns an `uncertain` receipt when a
request may have reached Redmine but a reliable response could not be obtained. Callers must
inspect uncertain results before trying again. Logs record method, status, and timing without
the request body, key, or response content. Live behavior still needs separate verification.

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
