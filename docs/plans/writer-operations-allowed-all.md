# Writer operation configuration follow-up

Date: 2026-10-06. Assignment: support `REDMINE_WRITER_OPERATIONS=allowed_all` without enumerating
individual write operations. Implementation finished; testing pending.

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
