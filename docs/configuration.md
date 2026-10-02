# Configuration

## Runtime settings

The application creates its settings when `create_app()` runs. Local execution reads `.env`
relative to the working directory, so start it from the repository root. Process environment
variables override `.env` values. Unrelated dotenv entries are ignored by the runtime settings.

| Variable | Default | Requirements and purpose |
|---|---|---|
| `REDMINE_URL` | Required | HTTP or HTTPS base URL reachable from MCP; no embedded credentials, query, or fragment. A deployment subpath is supported. |
| `REDMINE_WRITE_ENABLED` | `false` | Opt-in gate for future issue write routes; current release exposes only reads even when true. |
| `REDMINE_TIMEOUT_SECONDS` | `20` | Positive finite read/write timeout in seconds; an inactivity timeout, not an end-to-end deadline. |
| `REDMINE_CONNECT_TIMEOUT_SECONDS` | `5` | Positive finite connection timeout in seconds. |
| `REDMINE_POOL_TIMEOUT_SECONDS` | `5` | Positive finite connection-pool acquisition timeout in seconds. |
| `REDMINE_REQUEST_DEADLINE_SECONDS` | `60` | Positive finite deadline for each upstream HTTP read, including connection/pool waits and streamed body acquisition/closure. |
| `REDMINE_MAX_RESPONSE_BYTES` | `10485760` | Positive limit on accumulated decoded JSON payload bytes per upstream read. |
| `REDMINE_MAX_CONNECTIONS` | `100` | Positive maximum number of shared upstream connections. |
| `REDMINE_MAX_KEEPALIVE_CONNECTIONS` | `20` | Nonnegative idle connection limit; must not exceed maximum connections. |
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
Attachment binary reads prepared for the download tool have a fixed 5 MiB decoded-byte limit.
Their URLs must match the configured Redmine origin, deployment base path, and attachment ID;
redirects are rejected. The same per-read deadline applies, and the caller's personal key is
sent only after URL validation.
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

## Separate writer deployment prerequisite

The owner selected separate reader and writer deployments for future issue writes. Keep the
existing reader deployment read-only. A writer configuration uses `REDMINE_WRITE_ENABLED=true`
and a separate localhost `MCP_HOST_PORT`, such as `8001`. Each caller still supplies a personal
Redmine key. Future application permissions must also authorize writes. Never use an admin key.

Keep writer configuration in a separate ignored env-file and use a different Compose project name
so containers do not replace the reader deployment. The writer may use the same intended Redmine
URL. The flag is forwarded by base Compose and defaults false for existing deployments.
Future write routes must authenticate with a personal key and use `require_write_access`;
false returns `403` with `{"detail":"Write access is disabled"}`. Reader deployments must exclude
future writes from MCP discovery as well as reject direct REST mutations.

This prerequisite provides configuration and an authorization dependency only. No write route or
MCP tool is exposed yet. Application role rules, permission verification, and disposable data
remain separate work. The [MCP tool dashboard](plans/index.md)
tracks the reader-first release; writer tools are future ideas, not assigned tasks.
