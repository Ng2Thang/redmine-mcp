<p class="portal-eyebrow">Documentation / Redmine MCP</p>

# Understand the server. Use the tools. Follow the flow.

Redmine MCP exposes personal-key-authenticated Redmine operations through REST and MCP.
Start with installation, connect a client, then explore the architecture and development workflow.

<div class="portal-grid">
  <a class="portal-card" href="#/guides/installation"><strong>Get started</strong><span>Choose Docker or local Python and prepare your environment.</span></a>
  <a class="portal-card" href="#/guides/first-calls"><strong>Use the tools</strong><span>Make your first REST request and connect MCP Inspector.</span></a>
  <a class="portal-card" href="#/docs/mcp-request-flow"><strong>Trace execution</strong><span>Follow authentication, dispatch, Redmine access, and the response.</span></a>
  <a class="portal-card" href="#/guides/testing"><strong>Understand testing</strong><span>Explore the three testing layers, evidence, and authorization rules.</span></a>
</div>

See [visual tool examples](guides/visual-examples.md) for a sample prompt, tool call, result,
and a short animated walkthrough.

## Choose your reading path

| Your task | Start here | Continue with |
| --- | --- | --- |
| Install and connect | [Installation](guides/installation.md) | [First calls](guides/first-calls.md) |
| Configure access | [Reader and writer](guides/access.md) | [Configuration](docs/configuration.md) |
| Find inputs and results | [Tool reference](docs/tool-reference.md) | [Manual verification](docs/manual-verification.md) |
| Understand the implementation | [Module map](guides/module-map.md) | [Architecture](docs/architecture.md), [execution flow](docs/mcp-request-flow.md) |
| Add or change a tool | [Development](docs/development.md) | [Tool workflow](docs/workflows/redmine-tools.md) |
| Operate an environment | [Operations](docs/operations.md) | [Synthetic data](docs/test-data.md) |
| Review acceptance | [Testing overview](guides/testing.md) | [Coverage matrix](docs/plans/testing-coverage.md), [roadmap](docs/plans/index.md) |

## Current boundaries

The registered catalog contains **18 reads and 18 writes**. The default reader remains read-only;
writes require a separately enabled writer, configured operation gates, personal Redmine keys,
caller admission, and native permissions. The target Redmine version is **7.0.2**.

This is a development implementation for pilot evaluation. Dated testing records establish only
their recorded revisions and scenarios. Consult the [current roadmap](docs/plans/index.md) for
pending acceptance and waivers; the portal does not add production certification.

## About this portal

Detailed pages are exported from the repository's canonical `docs/` files. The introductory guides
and navigation live in `src/redmine_mcp_docs/`. Rendering, diagrams, and search use bundled local
assets. External links and commands that install packages or contact Redmine still need their own
network access.

See [portal maintenance and static deployment](docs/documentation-portal.md) and the
[manual portal checklist](guides/verification.md).
