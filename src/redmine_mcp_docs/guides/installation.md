# MCP server installation

Install and run the Redmine MCP server using Python or Docker. This is the server side:
the service that receives requests from your AI client and connects to Redmine.
If someone already operates it for you, ask for its URL and follow
[MCP client installation](get-started.md).

The application targets Redmine **7.0.2**. Commands use Git Bash on Windows and run from
the repository root. This guide describes setup; it does not run or authorize tests.

**Choose your setup**

| Your situation | Choose | What you need |
| --- | --- | --- |
| You have Redmine and want a local server | [Local Python](#local-python) | Git, Git Bash, Python 3.13, uv, access to Redmine |
| You want to explore sample data | [Docker with sample data](#docker-with-sample-data) | Git, Git Bash, Docker Desktop with Linux containers, Python 3.13, uv |
| You need Docker connected to your existing Redmine | [Docker with existing Redmine](#docker-with-existing-redmine) | Git, Git Bash, Docker Desktop with Linux containers, access to Redmine |

An AI client is needed to use MCP. Node.js/npm is only needed if you choose MCP Inspector.
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

## Docker with sample data

Start Docker Desktop, then run:

```bash
bash scripts/dev-up.sh
```

The helper creates private random credentials in `.env` when absent, starts services,
seeds sample data, and starts MCP. Use it only for the owned synthetic environment; keep
it separate from real Redmine configuration. Do not copy `.env.example` into this workflow.
Never run its seed/reset/restore helpers against a real Redmine instance.

| What to open | Default address |
| --- | --- |
| Sample Redmine | `http://localhost:3000` |
| Reader MCP URL | `http://localhost:8000/mcp` |
| REST API reference | `http://localhost:8000/docs` |

Follow [sample account access and lifecycle](../docs/operations.md) for credentials,
stop/restart, and sample-data management. Use the selected sample user's personal API key
when connecting; generated credentials must stay private.

Continue with [MCP client installation](get-started.md), using `http://localhost:8000/mcp`.

## Docker with existing Redmine

Use the [external Redmine deployment steps](../docs/operations.md#external-redmine) to prepare
`.local/external.env` and start the MCP-only Compose deployment. Docker Desktop must be running
with Linux containers. Do not use the sample environment's seed/reset/restore helpers here.

Then follow [MCP client installation](get-started.md), using your deployment's `/mcp` URL.

For startup problems, see [troubleshooting](troubleshooting.md). To enable changes later,
follow [reader and writer access](access.md); the writer is a separate deployment.
