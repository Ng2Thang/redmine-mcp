# Contributor documentation

For people developing, operating, or reviewing Redmine MCP. To use the product, start
with [MCP client installation](get-started.md) or [Everyday workflows](workflows.md).

Existing technical pages keep their original URLs. The user guide links to exact contracts
where needed, while implementation details and dated evidence remain available here.

## Develop tools

| Topic | Read |
| --- | --- |
| Repository quick start | [Repository README](../repository.md) |
| Architecture | [Module map](module-map.md), [Architecture](../docs/architecture.md) |
| Request execution | [MCP request and response flow](../docs/mcp-request-flow.md) |
| Development | [Development](../docs/development.md), [Contributing](../CONTRIBUTING.md) |
| Tool planning and implementation | [Tool workflow](../docs/workflows/redmine-tools.md), [Roadmap](../docs/plans/index.md) |
| Release history | [Changelog](../CHANGELOG.md) |

## Testing and evidence

Run checks only when separately assigned or approved. These links retain their original
dates, revisions, waivers, and scenario limits; this refresh runs no tests.

| Your goal | Read |
| --- | --- |
| Plan and run assigned checks | [Testing overview](testing.md), [testing roadmap](../docs/testing-roadmap.md), [coverage matrix](../docs/plans/testing-coverage.md) |
| Inspect MCP tools manually | [Manual tool verification](../docs/manual-verification.md) |

<details>
<summary>Recorded acceptance and review evidence</summary>

- [Earlier catalog acceptance](../docs/testing/evidence/current-catalog-acceptance.md)
- [Preparation regression evidence](../docs/testing/evidence/prep-022-026-testing.md)
- [Read retry evidence](../docs/testing/evidence/prep-027-testing.md)
- [Time-entry update evidence](../docs/testing/evidence/tool-042-testing.md)
- [Time-entry deletion evidence](../docs/testing/evidence/tool-043-testing.md)
- [Documentation audit](../docs/reviews/documentation-state-audit-2026-10-09.md)

</details>

## Operate and maintain the server

| Your goal | Read |
| --- | --- |
| Configure a server or writer | [Runtime settings](../docs/configuration.md), [reader and writer access](access.md) |
| Manage deployments and sample data | [Operations](../docs/operations.md), [synthetic data](../docs/test-data.md) |
| Review security or report a vulnerability | [Security policy](../SECURITY.md) |
| Serve or publish documentation | [Portal maintenance and deployment](../docs/documentation-portal.md) |
| Review the portal | [Portal manual checklist](verification.md), [earlier layout review](layout-review.md) |

User guides live in `src/redmine_mcp_docs/guides/`. Keep new Markdown in English, document
Bash commands, and label invented results as illustrative. Introduce goals and prerequisites,
then group prompts, steps, results, variations, and troubleshooting under three task-focused
headings per workflow. Keep implementation and testing histories in the linked contributor
references.
