# Configuration

## Runtime settings

The application creates its settings when `create_app()` runs. Local execution reads `.env`
relative to the working directory, so start it from the repository root. Process environment
variables override `.env` values. Unrelated dotenv entries are ignored by the runtime settings.

| Variable | Default | Requirements and purpose |
|---|---|---|
| `REDMINE_URL` | Required | HTTP or HTTPS URL of Redmine. Use the address reachable from the MCP process. |
| `REDMINE_API_KEY` | Required | API key for the shared Redmine account. Use a dedicated account with read-only permissions. |
| `MCP_API_TOKEN` | Required | Bearer token required by REST tools and MCP. Choose a long random secret. |
| `REDMINE_TIMEOUT_SECONDS` | `20` | Positive number of seconds for upstream HTTP operations. |
| `LOG_LEVEL` | `INFO` | Python logging level, such as `INFO` or `WARNING`. |

Secrets cannot be blank or begin with `replace-`. Values in `.env.example` are placeholders
and must be replaced for external use. Invalid required settings prevent application startup.
The internal MCP-to-REST client uses the configured timeout plus five seconds.

The MCP token and Redmine API key serve different purposes: clients send the MCP token;
the server uses the Redmine key upstream. All clients share that Redmine account's permissions.
See [security guidance](../SECURITY.md).

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

The script initially writes a bootstrap API-key placeholder and replaces it with the reader key
after seeding. Do not use that intermediate value to start a separate MCP process.
Generated state, credentials, manifests, and backups live in ignored `.local/`.

## Local and Docker addresses

| Caller | Redmine address |
|---|---|
| Local Python process using the synthetic environment | `http://localhost:3000` |
| MCP container with the synthetic Compose override | `http://redmine:3000` |
| Container accessing Redmine on the Windows host | Use `http://host.docker.internal:<port>` with the actual port. |

Base Compose passes the runtime settings from its interpolation environment into MCP.
The synthetic override explicitly replaces `REDMINE_URL` with the container service URL.
Compose shell variables can override values from `--env-file`; avoid stale exported credentials.

Published endpoints bind to localhost: MCP `8000`, Redmine `3000`, PostgreSQL `5433`.
PostgreSQL uses port `5432` inside Docker. MCP never connects to PostgreSQL.
Stop the MCP container before starting local Python on port `8000`.

## External Redmine

Create a separate ignored configuration file:

```bash
mkdir -p .local
cp -n .env.example .local/external.env
```

Edit `.local/external.env` privately and set the actual URL, read-only API key, and MCP token.
Base Compose only needs the five runtime settings; synthetic database/account values do not
configure external Redmine. Start MCP using the [operations guide](operations.md).

Do not run seed, reset, or restore against an external instance. Do not disable TLS verification.
Do not share `docker compose config` output because interpolation can expose secrets.
