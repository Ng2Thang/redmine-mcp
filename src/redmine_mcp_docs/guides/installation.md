# MCP server installation

Install and run the Redmine MCP server using Python or Docker. This is the server side:
the service that receives requests from your AI client and connects to Redmine.
If someone already operates it for you, ask for its URL and follow
[MCP client installation](get-started.md).

The primary target is Redmine **7.0.2**. Built-in development and E2E profiles are available
for **6.0.1 and 7.0.2**. Commands use Git Bash on Windows and run from the repository root.
This guide describes setup; use [Testing and evidence](testing.md) for automated test runs.

**Choose your setup**

| Your situation | Choose | What you need |
| --- | --- | --- |
| You have Redmine and want a local server | [Local Python](#local-python) | Git, Git Bash, Python 3.13, uv, access to Redmine |
| You want to explore sample data | [Docker with sample data](#docker-with-sample-data) | Git, Git Bash, Docker Desktop with Linux containers, Python 3.13, uv |
| You need Docker connected to your existing Redmine | [Docker with existing Redmine](#docker-with-existing-redmine) | Git, Git Bash, Docker Desktop with Linux containers, access to Redmine |

An AI client is needed to use MCP. Node.js/npm is needed for MCP Inspector, including
the automated E2E suite's Inspector cases. Sample stacks require Docker Compose 2.24.4+.
Initial dependency and image downloads require Internet access.

**Get the source once**, before following your chosen setup:

If you do not already have a checkout:

```bash
git clone https://github.com/Ng2Thang/redmine-mcp.git
cd redmine-mcp
```

Otherwise, open Git Bash in your existing repository root.

## Local Python

Install the locked dependencies and start the reader. Replace the example with the URL
your server process can reach, including any deployment subpath. A personal API key is supplied by the client
later; no shared API key is needed here.

```bash
uv sync --frozen
export REDMINE_URL='https://redmine.example.com'
export REDMINE_WRITE_ENABLED=false
uv run --frozen uvicorn redmine_mcp.app:create_app --factory --host 127.0.0.1 --port 8000 --no-access-log
```

Leave the terminal open. Press Ctrl+C to stop. Environment settings apply to this shell;
for persistent `.env` configuration and other options, see
[runtime settings](../docs/configuration.md). Do not put credentials in the Redmine URL.

If another process uses port 8000, stop it first or select a different `--port` and use
that port in your client. Stop the Docker MCP service before using its port locally.

Continue with [MCP client installation](get-started.md), using `http://127.0.0.1:8000/mcp`.

### Start from an existing `.env`

If the repository root already contains your configured `.env`, open a fresh Git Bash
terminal there and run:

```bash
uv sync --frozen
REDMINE_WRITE_ENABLED=false uv run --frozen uvicorn redmine_mcp.app:create_app --factory --host 127.0.0.1 --port 8000 --no-access-log
```

The application loads `.env` automatically. Set `REDMINE_URL` to the Redmine address
reachable from Windows; `REDMINE_URL_LOCAL` is not a runtime setting. Exported shell
variables take precedence over `.env`. The command above explicitly starts a reader,
even if the file contains `REDMINE_WRITE_ENABLED=true`.

For a new external-instance configuration, copy `.env.example` to `.env` only if no
`.env` exists, then edit `REDMINE_URL` before starting. Keep personal API keys in your
client's private `X-Redmine-API-Key` header settings.

The MCP endpoint is `http://127.0.0.1:8000/mcp`, and the REST reference is
`http://127.0.0.1:8000/docs`. Local Python uses the command's `--port`; `MCP_HOST_PORT`
and `MCP_WRITER_HOST_PORT` configure Docker Compose ports only.

Leave this terminal open while using MCP. Stop with Ctrl+C, then rerun the startup
command to restart or apply `.env` changes. Writer setup is documented under
[reader and writer access](access.md).

## Docker with sample data

Start Docker Desktop, then run:

```bash
bash scripts/dev-up.sh 7.0.2
bash scripts/dev-up.sh 6.0.1
```

Choose either command, or run both for independent environments. Omitting the argument
defaults to 7.0.2. Each version uses a self-contained Compose file with fixed local settings;
root `.env` is ignored, and no host env file or seed-state directory is created. The helper
starts PostgreSQL/Redmine, seeds the baseline and history datasets, and starts the MCP reader.
It checks for occupied ports before startup and reuses services belonging to the selected project.

| Setting | Redmine 7.0.2 | Redmine 6.0.1 |
| --- | --- | --- |
| Compose project | `redmine-mcp-dev-7-0-2` | `redmine-mcp-dev-6-0-1` |
| Sample Redmine | `http://localhost:8001` | `http://localhost:3001` |
| Reader MCP URL | `http://localhost:8000/mcp` | `http://localhost:8002/mcp` |
| REST API reference | `http://localhost:8000/docs` | `http://localhost:8002/docs` |
| PostgreSQL | `localhost:5433` | `localhost:5436` |

Demo accounts use password `redmine-demo-password`. Database/user are `redmine`, with
password `redmine-local-development`. These fixed credentials belong only to localhost
development stacks. Docker stores database, attachments, and seed state in named volumes.
Old test projects and their data remain separate; stop a conflicting old service if startup
identifies it. Never run synthetic seed/reset/restore helpers against real Redmine data.

Follow [sample account access and lifecycle](../docs/operations.md) for credentials,
stop/restart, and sample-data management. Use the selected sample user's personal API key
when connecting; personal API keys and private seed manifests must stay private.

Continue with [MCP client installation](get-started.md), using the reader URL for your version.
To run automated E2E, follow [Testing and evidence](testing.md). E2E prepares its own
fixtures automatically; development startup and the large demo/history datasets are optional.

## Docker with existing Redmine

Start Docker Desktop with Linux containers. Prepare a separate configuration once:

```bash
mkdir -p .local
cp -n .env.example .local/external.env
```

Edit `.local/external.env` and set `REDMINE_URL` to an address reachable from the container.
For Redmine on the Windows host, use `http://host.docker.internal:3000`, replacing the port
with your Redmine port. For a remote instance, use its actual HTTPS URL. Set
`REDMINE_PUBLIC_URL`, if needed, to the address users open in their browser, and keep
`REDMINE_TEST_MARKER` blank for a real instance.

Start the MCP reader from the repository root:

```bash
export MSYS_NO_PATHCONV=1
export MSYS2_ARG_CONV_EXCL='*'
docker compose -p redmine-mcp-external --env-file .local/external.env -f deploy/compose.yaml up -d --build mcp-server
```

Docker runs the server in the background. With the default `MCP_HOST_PORT=8000`, connect
to `http://127.0.0.1:8000/mcp`. Base Compose keeps this service read-only. Use the separate
[writer deployment](../docs/operations.md#separate-writer) for write actions, with a distinct
`MCP_WRITER_HOST_PORT` such as `8001` when the reader uses `8000`.

View startup logs or stop the reader with:

```bash
docker compose -p redmine-mcp-external --env-file .local/external.env -f deploy/compose.yaml logs --follow --tail=100 mcp-server
docker compose -p redmine-mcp-external --env-file .local/external.env -f deploy/compose.yaml stop mcp-server
```

Press Ctrl+C to leave the log viewer; the container keeps running. Rerun the startup
command to start a stopped reader or apply configuration changes. This deployment starts
MCP only and connects to your existing Redmine. See the
[external Redmine deployment steps](../docs/operations.md#external-redmine) for more details.

Then follow [MCP client installation](get-started.md), using your deployment's `/mcp` URL.

For startup problems, see [troubleshooting](troubleshooting.md). To enable changes later,
follow [reader and writer access](access.md); the writer is a separate deployment.
