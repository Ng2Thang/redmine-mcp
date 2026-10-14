# Contributor documentation

For people developing, operating, or reviewing Redmine MCP. To use the product, start
with [MCP client installation](get-started.md) or [Everyday workflows](workflows.md).

Sidebar pages and the earlier Overview's reference pages are published. Retained
references open locally; other technical records open repository files on GitHub.

## Develop tools

| Topic | Read |
| --- | --- |
| Repository quick start | [Repository README](https://github.com/Ng2Thang/redmine-mcp/blob/master/README.md) |
| Architecture | [Module map](module-map.md), [Architecture](../docs/architecture.md) |
| Request execution | [MCP request and response flow](../docs/mcp-request-flow.md) |
| Development | [Development](../docs/development.md), [Contributing](https://github.com/Ng2Thang/redmine-mcp/blob/master/CONTRIBUTING.md) |
| Tool planning and implementation | [Tool workflow](../docs/workflows/redmine-tools.md), [Roadmap](../docs/plans/index.md) |
| Release history | [Changelog](https://github.com/Ng2Thang/redmine-mcp/blob/master/CHANGELOG.md) |

## Testing and evidence

Run checks only when separately assigned or approved. These links retain their original
dates, revisions, waivers, and scenario limits; this refresh runs no tests.

| Your goal | Read |
| --- | --- |
| Plan and run assigned checks | [Testing overview](testing.md), [canonical testing roadmap](https://github.com/Ng2Thang/redmine-mcp/blob/master/docs/testing-roadmap.md), [coverage matrix](../docs/plans/testing-coverage.md) |
| Inspect MCP tools manually | [Manual tool verification](../docs/manual-verification.md) |

Default `uv run --frozen pytest` selects offline unit/integration tests. Authorized live runs
select `tests/e2e --run-e2e` with `REDMINE_E2E_VERSION=6.0.1` or `7.0.2`; pytest prepares
the selected development stack automatically. The built-in projects need no env file.
See [test commands and state](testing.md#commands-for-an-authorized-assignment) for
private directories, focused runs, supplemental tools, and reset boundaries.

<details>
<summary>Recorded acceptance and review evidence</summary>

- [Earlier catalog acceptance](https://github.com/Ng2Thang/redmine-mcp/blob/master/docs/testing/evidence/current-catalog-acceptance.md)
- [Preparation regression evidence](https://github.com/Ng2Thang/redmine-mcp/blob/master/docs/testing/evidence/prep-022-026-testing.md)
- [Read retry evidence](https://github.com/Ng2Thang/redmine-mcp/blob/master/docs/testing/evidence/prep-027-testing.md)
- [Time-entry update evidence](https://github.com/Ng2Thang/redmine-mcp/blob/master/docs/testing/evidence/tool-042-testing.md)
- [Time-entry deletion evidence](https://github.com/Ng2Thang/redmine-mcp/blob/master/docs/testing/evidence/tool-043-testing.md)
- [Documentation audit](https://github.com/Ng2Thang/redmine-mcp/blob/master/docs/reviews/documentation-state-audit-2026-10-09.md)
- [Repository and documentation audit (2026-10-14)](https://github.com/Ng2Thang/redmine-mcp/blob/master/docs/reviews/repository-docs-audit-2026-10-14.md)

</details>

## Operate and maintain the server

| Your goal | Read |
| --- | --- |
| Configure a server or writer | [Runtime settings](../docs/configuration.md), [reader and writer access](access.md) |
| Manage deployments and sample data | [Operations](../docs/operations.md), [synthetic data](../docs/test-data.md) |
| Review security or report a vulnerability | [Security policy](https://github.com/Ng2Thang/redmine-mcp/blob/master/SECURITY.md) |
| Serve or publish documentation | [Portal maintenance and deployment](../docs/documentation-portal.md) |
| Review the portal | [Portal manual checklist](verification.md), [source maintenance guide](https://github.com/Ng2Thang/redmine-mcp/blob/master/src/redmine_mcp_docs/README.md), [earlier documentation audit](https://github.com/Ng2Thang/redmine-mcp/blob/master/docs/reviews/documentation-state-audit-2026-10-09.md) |

User guides live in `src/redmine_mcp_docs/guides/`. Keep all Markdown in English, document
Bash commands, and label invented results as illustrative. Introduce goals and prerequisites,
then group prompts, steps, results, variations, and troubleshooting under three task-focused
headings per workflow. Keep implementation and testing histories in the linked contributor
references.
