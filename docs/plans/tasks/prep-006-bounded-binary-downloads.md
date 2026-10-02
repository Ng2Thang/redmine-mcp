# prep-006-bounded-binary-downloads: Add bounded binary reads

## 1. Task identity and status

| Field | Value |
|---|---|
| Task ID | prep-006-bounded-binary-downloads |
| Assigned capability | Prepare shared attachment download transport for tool-019. |
| Type / access / destructive effects | Shared prerequisite / infrastructure / no direct Redmine mutation; later downloads can increment counters |
| Status | blocked - implementation finished; testing pending |
| Dependencies | [tool-018-get-attachment](tool-018-get-attachment.md); predecessor acceptance required |
| Related tasks | [Master plan](../redmine-7-0-2-capabilities.md); [dashboard](../index.md) |
| Target Redmine version | 7.0.2-bookworm pinned in synthetic Compose; runtime acceptance pending |
| Last updated | 2026-10-02, Codex |
| Progress summary | Validated same-origin attachment URL and bounded binary streaming implemented in the Redmine client; the shared decoded-byte limit is configurable and defaults to 5 MiB. |
| Blocker / next action | User approved this implementation and directed continuation to tool-019 on 2026-10-02. Offline URL/stream/error checks require separate authorization; live 7.0.2 behavior remains unverified. |

## 2. Discovery and evidence

Prepare shared attachment download transport for tool-019. Use the caller's key on validated Redmine-origin URLs; reject redirects and mismatched base paths; stream with deadline and 5 MiB decoded limit; avoid logging bytes or keys; preserve JSON transport behavior.

| Source | Checked | Evidence and limitation |
|---|---|---|
| [Current roadmap](../index.md) | 2026-10-01 | Existing task status and architecture; no pending acceptance is treated as passed. |
| [Repository pin](../../../deploy/compose.test.yaml) | 2026-10-02 | Redmine 7.0.2 is pinned; runtime acceptance remains pending. |
| [Tool reference](../../tool-reference.md) | 2026-10-01 | Existing public catalog is the compatibility baseline. |
| [Exact release archive](https://www.redmine.org/releases/redmine-7.0.2.tar.gz) | 2026-10-02 | `render_api_attachment_attributes` emits an absolute `download_named_attachment_url`; `AttachmentsController#download` increments Project/Version download counters before sending bytes. This source does not prove the deployment's generated URL origin matches `REDMINE_URL`. |

Decisions: this prerequisite owns no public MCP operation. The user approved tool-018 and
directed continuation on 2026-10-02. Download transport accepts only URLs with the configured
Redmine origin, base path, and requested attachment ID. A deployment whose generated absolute
content URL uses another origin must align its Redmine URL configuration before downloading;
the transport will not send a personal key to an unconfigured origin. Testing and live rehearsal
require separate user authorization.

## 3. Requirements

| Requirement | Observable behavior |
|---|---|
| REQ-001 | Prepare shared attachment download transport for tool-019. |
| REQ-002 | Use the caller's key on validated Redmine-origin URLs; reject redirects and mismatched base paths; stream with deadline and 5 MiB decoded limit; avoid logging bytes or keys; preserve JSON transport behavior. |
| REQ-003 | Scope and existing capability compatibility are preserved; evidence is dated and redacted. |

In scope: Shared Redmine transport and configuration only; no MCP operation. Out of scope: unrelated Redmine APIs, an administrator
production credential, and claims based on unrun checks.

## 4. Public contract and technical specification

| Area | Contract |
|---|---|
| MCP name / operation ID / REST route | N/A - shared prerequisite |
| Inputs | `content_url` from Redmine metadata, positive attachment ID, caller-bound client; configurable decoded limit defaulting to 5 MiB and existing per-read deadline |
| Outputs | Valid download returns exact bytes. The URL must have the configured scheme, host, port, base path, and `/attachments/download/{id}` prefix, without credentials, query, fragment, or traversal. Redirects, oversize, timeout, and malformed URLs fail with sanitized errors. Existing JSON reads remain unchanged. |
| Access | No new public permission |
| Version support | Exact 7.0.2 source reviewed; generated URL origin and runtime behavior remain unverified. |
| Errors | Record failed prerequisite or recovery as blocked; never fabricate a successful result. |

Write semantics: N/A for this unexposed transport prerequisite. When called by tool-019, Redmine
may increment Project/Version download counters even if the eventual byte transfer fails.

Specification exit check: the exact version source supports the attachment URL shape and counter
effect; runtime and offline acceptance remain pending.

## 5. Implementation plan

1. Inspect the predecessor's accepted evidence and current configuration.
2. Review authoritative versioned source or repository contracts relevant to this prerequisite.
3. Use the caller's key on validated Redmine-origin URLs; reject redirects and mismatched base paths; stream with deadline and 5 MiB decoded limit; avoid logging bytes or keys; preserve JSON transport behavior.
4. Update only the owned implementation or operations documentation; preserve unrelated edits.
5. Run applicable static checks during a separately assigned coding stage.
6. Hand off exact offline and synthetic scenarios; run them only with separate testing authorization.
7. Update this task and the dashboard from actual results, then request user acceptance.

## 6. Acceptance criteria and traceability

| Criterion | Requirement | Observable result | Evidence |
|---|---|---|---|
| AC-001 | REQ-001 | Prepare shared attachment download transport for tool-019. | Pending |
| AC-002 | REQ-002 | Valid download returns exact bytes; redirects/oversize/timeout/malformed URL fail safely; existing JSON reads remain compatible. | Pending |
| AC-003 | REQ-003 | Existing tools and unrelated state remain compatible; failures are reported. | Pending |

Each criterion requires a dated procedure and redacted actual result. A draft
or static check alone does not pass acceptance.

## 7. Test plan and execution record

Testing is planned, not authorized or run. For prep-006-bounded-binary-downloads, verify:
- Success: Valid download returns exact bytes; redirects/oversize/timeout/malformed URL fail safely; existing JSON reads remain compatible.
- Failure: unavailable artifact, rejected permission, malformed response,
  timeout, or failed recovery as applicable; record a blocker.
- Compatibility: compare existing reader catalog and outcomes before/after.
- Synthetic: use the marked isolated environment only after separate authorization.

| Evidence ID | Procedure | Actual result | Status |
|---|---|---|---|
| EVID-001 | Ruff lint/format, mypy, and `git diff --check` during coding | Installed Ruff lint passed; format found 161 files formatted; mypy passed for 85 source files; whitespace check passed on 2026-10-02. | Passed via installed executables |
| EVID-002 | `uv run --frozen pytest` only after explicit testing authorization, when applicable | Not run | Pending |
| EVID-003 | Inspector and synthetic procedure only after explicit authorization | Not run | Pending |

## 8. Implementation and review record

- Changes made: added attachment URL validation and bounded `get_attachment_bytes` to
  `RedmineClient`, plus configuration and changelog docs. Follow-up on 2026-10-02: wired
  `REDMINE_MAX_BINARY_BYTES` through Settings and Compose so uploads and downloads can share
  the configurable 5 MiB default required by the master roadmap.
- Static checks: installed `.venv/Scripts/ruff.exe check .`, `.venv/Scripts/ruff.exe format
  --check .`, `.venv/Scripts/mypy.exe src`, and `git diff --check` passed on 2026-10-02.
- Automated tests: not run.
- Startup, Inspector, and live state checks: not run.
- Final diff review: the new binary method and fixed policy bound are isolated from the
  existing JSON `get` method; no public operation or read-policy setting changed.
- Remaining verification: exact URL acceptance/rejection; mismatched origin/base path/ID;
  redirect and upstream status mapping; `Content-Length` and streamed decoded-byte limits;
  timeout, connection failure, guaranteed stream closure, and unchanged JSON behavior.

## 9. Completion and handoff

- [x] Required prerequisite implemented or performed.
- [ ] Acceptance criteria have passing evidence.
- [x] Applicable static checks pass; offline and runtime verification remain pending.
- [ ] Compatibility and recovery/state checks pass where relevant.
- [x] Dashboard and documentation match actual evidence.
- [x] User approved this implementation and directed continuation to tool-019 on 2026-10-02.

Final status: implementation finished; user review approved; testing pending. Next action:
execute the planned offline and synthetic checks after separate testing authorization.

Target record (2026-10-02): Redmine 7.0.2 is the sole supported release. Prior runtime observations do not establish acceptance for the pinned target.
