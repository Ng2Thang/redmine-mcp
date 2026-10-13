# Writer operation configuration follow-up

> Writer admission update (2026-10-13): pinned-key and user ID admission checks
> are retired. Earlier requirements and evidence below describe historical behavior.
> See [current configuration](../configuration.md#separate-writer-deployment).

Date: 2026-10-06. Assignment: support `REDMINE_WRITER_OPERATIONS=allowed_all` without enumerating
individual write operations. Implementation finished; testing pending.

Current reconciliation, 2026-10-07: [prep-020](tasks/prep-020-current-catalog-acceptance.md)
verifies the sentinel with the current 15 writers. The original coding-only record below is
preserved; it is not the current testing status.

## Contract and implementation

- Standalone lowercase `allowed_all`, with optional surrounding whitespace, expands to
  `WRITE_OPERATIONS` in `Settings.writer_operations`. Mixed sentinel/CSV lists are rejected
  when the writer is enabled. Empty values and explicit operation lists retain their behavior.
- Existing MCP registration, REST admission and capability reporting consume the expanded set.
  Writer enablement, identity restrictions, caller permissions and Redmine authorization remain
  required. Future registered operations are included after a server upgrade.
- Updated configuration documentation, the environment template comments and changelog.
  Deployed settings and live Redmine memberships were not changed.

## Acceptance handoff

No tests, startup checks, Inspector calls or live mutations are authorized by this assignment.
Later authorized verification should cover all registered MCP writes with `allowed_all`, REST
admission and capabilities, reader write denial, identity restrictions, project permissions,
whitespace, invalid mixed lists, unknown names, empty defaults and explicit CSV compatibility.
Use offline settings/catalog/authorization coverage first; live verification requires the owned
synthetic writer environment and task-owned cleanup for any mutations.

Static-check evidence on 2026-10-06: Git Bash prerequisite doctor passed;
`uv run --frozen --no-sync ruff check .` passed; `uv run --frozen --no-sync mypy src`
passed for 118 source files. The initial formatting check identified one condition to reformat;
the condition was formatted. Final `uv run --frozen --no-sync ruff check .` passed,
`uv run --frozen --no-sync ruff format --check .` passed for 235 files,
`uv run --frozen --no-sync mypy src` passed for 118 source files and `git diff --check` passed.

Final diff review: configuration expansion feeds existing catalog/admission consumers; no
authorization bypass, credential changes or test edits were introduced. Pre-existing membership
implementation changes in the working tree were preserved.

## Authorized prep-020 acceptance, 2026-10-07

The user assigned prep-020 after prep-019 testing. Settings cases cover standalone/whitespace,
mixed/duplicated/trailing/uppercase sentinel rejection, empty and explicit CSV compatibility.
Unknown valid-looking operation names are rejected by catalog validation at application startup,
rather than by the Settings syntax validator. All 15 writers pass through REST and MCP under
`allowed_all`. Personal/pinned identity, restricted IDs, wrong pinned key, reader deployment and
project-role denials remain enforced. Disabled/denied capability candidates are omitted by
operation filtering, rather than reported as grants.

The full offline suite passes 1086 cases. Owned 7.0.2 version/membership state checks pass;
Inspector 2.8.0 verifies the expanded catalog, writer schema/annotations and three native-parity
read calls. Disposable project/role cleanup passes. The sentinel does not modify native grants,
enable production writes, or provide unconditional permissions. See the [current ledger](../testing/evidence/current-catalog-acceptance.md)
for final cross-catalog execution and original historical limitations.
