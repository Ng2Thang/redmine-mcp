# Installation

Choose an owned synthetic Docker environment for evaluation, or run Python locally against a
Redmine instance you can access. The application targets Redmine 7.0.2. Use Git Bash on Windows
and run the following commands from the repository root.

## Prerequisites

| Component | Purpose |
| --- | --- |
| Git Bash and Git | Repository commands and Bash helpers |
| Python 3.13 and uv | Local development and locked Python dependencies |
| Docker Desktop with Linux containers | Synthetic Redmine/PostgreSQL/MCP environment |
| Node.js/npm | MCP Inspector, when you choose to use it |

The documentation portal itself uses Python's standard library, local browser assets, and Git
for export inventory. It needs no Docker, Node installation, API key, or running Redmine server.

## Option A: synthetic Docker environment

```bash
bash scripts/dev-up.sh
```

The helper generates private random credentials in `.env` when absent, starts the synthetic
services, seeds sample data, and starts MCP. Image downloads and the initial build need Internet
access. Do not copy `.env.example` into this workflow or mix real-server configuration into it.

| Service | Default address |
| --- | --- |
| Redmine | `http://localhost:3000` |
| Swagger | `http://localhost:8000/docs` |
| MCP Streamable HTTP | `http://localhost:8000/mcp` |
| Liveness | `http://localhost:8000/health` |
| PostgreSQL host port | `5433` |

See [operations](../docs/operations.md) for account access, stop/restart, seeding, and data helpers.
Never run synthetic seed/reset/restore helpers against a real Redmine instance.

## Option B: local Python

Prepare prerequisites and locked dependencies:

```bash
bash scripts/doctor.sh
uv sync --frozen
```

Follow [external Redmine configuration](../docs/configuration.md#external-redmine) to supply a
reachable `REDMINE_URL`. Local settings are loaded at application creation from the repository
root's `.env`, with process environment values taking precedence. Credentials are supplied by
each client request, rather than by a global runtime API key setting.

Stop the Docker MCP service before using its port locally. Then start the reader:

```bash
uv run --frozen uvicorn redmine_mcp.app:create_app --factory --host 127.0.0.1 --port 8000 --reload --no-access-log
```

Swagger remains at `/docs`; this documentation portal runs on its own listener. Installation
does not imply testing authorization. Run quality tooling or tests only within an assignment
that permits those checks.

## Open this documentation portal

```bash
bash scripts/docs-portal.sh serve
```

Open `http://127.0.0.1:8080/`. An optional port avoids a local conflict:

```bash
bash scripts/docs-portal.sh serve 8088
```

Press Ctrl+C to stop. The helper exports current documentation before starting; restart it
after edits. Browser rendering, search, highlighting, and diagrams work without Internet access.
This does not make Redmine requests or dependency-installation commands work offline.

Continue with [first calls](first-calls.md) or [reader and writer access](access.md).
