# Writer admission simplification

Date: 2026-10-13. Status: implementation complete; functional verification deferred.

## Requested behavior

Remove the writer's pinned-key hash and user ID admission list. The user explicitly chose
to retain `REDMINE_WRITER_OPERATIONS`. Every REST and MCP caller still authenticates with a
personal Redmine API key, and native Redmine permissions remain authoritative.

Writes require `REDMINE_WRITE_ENABLED=true` and an enabled operation. Readers remain read-only.
The writer's resource checks, capability reports and MCP discovery use each caller's own
identity and target permissions. There is no separate list of admitted keys or users.

## Implementation

- Remove writer authentication mode, key digest and user ID settings and validation.
- Remove admission checks from REST authentication, write access, container capability scope
  and MCP discovery. Use caller resource authorization for every enabled writer.
- Remove the retired settings from Compose and environment examples. Existing private values
  are ignored by settings; remove them when migrating and recreate or restart the deployment.
- Remove raw key debug prints from authentication.
- Update unit, integration and E2E fixtures and scenarios. Successful writer coverage includes
  a rotated valid key and a second user with the necessary permissions. Retain missing/invalid
  credentials, disabled writers, operation ceilings and native permission denial scenarios.
- Update current documentation and mark superseded plans and evidence as historical.

## Verification handoff

Tests were updated but not executed. No application startup, Inspector calls, live writes,
deployment or private environment changes were performed. Historical passing test counts do
not establish acceptance of this change.

Ruff lint and formatting pass for changed Python files. The full `mypy src` check reports
four errors in unchanged documentation tooling: `redmine_mcp_docs/tools/portal.py` at lines
184, 223 and 238, and `redmine_mcp_docs/tools/vendor_assets.py` at line 24. These remain outside
this writer admission change.

`mypy src/redmine_mcp` passes for 130 source files. A broader Ruff check of the runtime reports
four existing style errors in unchanged files: import ordering in `api/dependencies.py`,
`features/attachments/router.py` and `integrations/redmine/retry.py`, and a long line in
`features/users/capability_service.py`. No runtime or test execution is implied by static checks.

For a separately authorized test run, use the existing locked offline fixtures first. Live
verification must use the owned synthetic environment and ordinary caller credentials. Check
that two users with sufficient target permissions can attempt configured writes, while a
user without the required native permissions is denied. Also cover reader writes, disabled
operations, empty operation lists, invalid/duplicate keys, session ownership and key rotation.

See [configuration](../configuration.md#separate-writer-deployment) and the
[testing roadmap](../testing-roadmap.md).
