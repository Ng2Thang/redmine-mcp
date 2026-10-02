# prep-005-upgrade-redmine-7-1: Pin and rehearse Redmine 7.0.2

The task ID is retained for existing links. Its active target changed to 7.0.2 on
2026-10-02 at the user's request.

## 1. Task identity and status

| Field | Value |
|---|---|
| Task ID | prep-005-upgrade-redmine-7-1 |
| Assigned capability | Prepare the exact 7.0.2 target and an isolated, recoverable upgrade rehearsal. |
| Type / access / destructive effects | Shared prerequisite / isolated migration rehearsal / Database migration in isolated copy |
| Status | blocked - implementation finished; testing pending |
| Dependencies | [prep-004-accept-existing-baseline](prep-004-accept-existing-baseline.md); predecessor acceptance required |
| Related tasks | [Master plan](../redmine-7-1-capabilities.md); [dashboard](../index.md) |
| Target Redmine version | 7.0.2-bookworm pinned by digest in isolated Compose; original synthetic instance remains 6.0.5-bookworm |
| Last updated | 2026-10-02, Codex |
| Progress summary | Official 7.0.2 source checksum and registry digest verified; isolated candidate/recovery Compose and guarded restore helpers prepared. No migration or recovery has run. |
| Blocker / next action | Separately authorize and execute the PREP-005 isolated backup, migration, reader/API comparison and independent recovery scenarios. |

## 2. Discovery and evidence

Prepare the exact 7.0.2 target and an isolated, recoverable upgrade rehearsal. Check
runtime/plugin requirements; back up database and files; migrate an isolated copy;
verify existing MCP tools, supported Files/Attachments/Issues REST, API-key auth,
and recovery from backup. Documents REST is outside this target.

| Source | Checked | Evidence and limitation |
|---|---|---|
| [Redmine upgrade guide](https://www.redmine.org/projects/redmine/wiki/RedmineUpgrade) | 2026-10-01 | Backup, requirements, migrations, and recovery are required. |
| [Repository pin](../../../deploy/compose.test.yaml) | 2026-10-01 | Original synthetic Redmine is 6.0.5; this remains the source baseline. |
| [Tool reference](../../tool-reference.md) | 2026-10-01 | Existing public catalog is the compatibility baseline. |
| [Official downloads](https://www.redmine.org/projects/redmine/wiki/Download) | 2026-10-02 | Released 7.0.2 tarball SHA-256: `d45e6d4c373cc3c8d33f1f4d4a2ffae1e1adb18703160707467493de7b4be591`. |
| [Official Docker image](https://hub.docker.com/_/redmine) | 2026-10-02 | `7.0.2-bookworm` published; `docker buildx imagetools inspect` returned index digest `sha256:5cb12288dbfb807f136adbee02d60a96acc24edad0404cbfce214a7ced39ff6a`. |
| [Isolated target](../../../deploy/compose.redmine-7-0-2.yaml) | 2026-10-02 | Reader-only candidate with separate Compose project, volumes and localhost ports; not started. Candidate and recovery PostgreSQL images are pinned to locally cached 16.8 index digest `sha256:301bcb60b8a3ee4ab7e147932723e3abd1cef53516ce5210b39fd9fe5e3602ae`. |
| [Versioned 7.0.2 source](https://www.redmine.org/releases/redmine-7.0.2.tar.gz) | 2026-10-02 | Downloaded into ignored `.local/`; SHA-256 matches official release and image Dockerfile. Gemfile requires Ruby >=3.2 and <4.1, Rails 8.1.4. Documents controller has HTML rendering/redirects; Enumerations index accepts API authentication and API output. |
| [Pinned image Dockerfile](https://github.com/docker-library/redmine/blob/df0d3284a3da8a77363a086cecba5eeed7f4f1f9/7.0/bookworm/Dockerfile) and [entrypoint](https://github.com/docker-library/redmine/blob/df0d3284a3da8a77363a086cecba5eeed7f4f1f9/docker-entrypoint.sh) | 2026-10-02 | Uses Ruby 4.0; normal startup runs `db:migrate` unless `REDMINE_NO_DB_MIGRATE` is set. Candidate Compose disables automatic migration. |
| [Redmine installation requirements](https://www.redmine.org/projects/redmine/wiki/RedmineInstall) | 2026-10-02 | Redmine 7.0 recommends PostgreSQL 14 or later; candidate retains PostgreSQL 16.8. |

The user directed continuation to PREP-005 on 2026-10-02, accepting PREP-004's revised
offline baseline. This authorizes independent implementation documentation, not testing or
live migration. See the [upgrade and recovery runbook](../../redmine-upgrade.md).

Decisions: this prerequisite owns no public MCP operation; prep-004-accept-existing-baseline must be
reviewed without rewriting prior evidence. Testing and any live rehearsal
require separate user authorization. The exact build remains an execution
blocker where version-specific behavior is needed. The user retargeted this task to
7.0.2 on 2026-10-02; its legacy ID remains stable for links.

## 3. Requirements

| Requirement | Observable behavior |
|---|---|
| REQ-001 | Prepare an exact 7.0.2 target and an isolated, recoverable upgrade rehearsal. |
| REQ-002 | Select a released artifact and immutable image digest; check runtime/plugin requirements; back up database and files; migrate an isolated copy; verify existing MCP tools, supported REST, API-key auth, and recovery from backup. |
| REQ-003 | Scope and existing capability compatibility are preserved; evidence is dated and redacted. |

In scope: Deployment/test configuration and migration runbook; no public MCP operation. Out of scope: unrelated Redmine APIs, an administrator
production credential, and claims based on unrun checks.

## 4. Public contract and technical specification

| Area | Contract |
|---|---|
| MCP name / operation ID / REST route | N/A - shared prerequisite |
| Inputs | Released 7.0.2 artifact and digest, backup manifest, isolated database and file volumes |
| Outputs | Pinned digest and versioned source; backup and restore logs; migration and old-tool evidence; no damage to the original 6.0.5 environment. |
| Access | Synthetic environment only; never overwrite the original instance |
| Version support | 7.0.2-bookworm pinned; runtime acceptance evidence is required before completion. |
| Errors | Record failed prerequisite or recovery as blocked; never fabricate a successful result. |

Write semantics: Migration may be irreversible on the migrated copy. Restore from the pre-upgrade database and attachment backups; never claim image downgrade reverses migrations.

Specification exit check: the prerequisite's procedure and expected evidence
are assigned. The image is pinned; execution evidence remains pending.

## 5. Implementation plan

1. Inspect the predecessor's accepted evidence and current configuration.
2. Review authoritative versioned source or repository contracts relevant to this prerequisite.
3. Use the pinned 7.0.2 image; check runtime/plugin requirements; back up database and files; migrate an isolated copy; verify existing MCP tools, supported REST, API-key auth, and recovery from backup.
4. Update only the owned implementation or operations documentation; preserve unrelated edits.
5. Run applicable static checks during a separately assigned coding stage.
6. Hand off exact offline and synthetic scenarios; run them only with separate testing authorization.
7. Update this task and the dashboard from actual results, then request user acceptance.

## 6. Acceptance criteria and traceability

| Criterion | Requirement | Observable result | Evidence |
|---|---|---|---|
| AC-001 | REQ-001 | Prepare an exact 7.0.2 target and an isolated, recoverable upgrade rehearsal. | Pending |
| AC-002 | REQ-002 | Pinned digest and versioned source; backup and restore logs; migration and old-tool evidence; no damage to the original 6.0.5 environment. | Pending |
| AC-003 | REQ-003 | Existing tools and unrelated state remain compatible; failures are reported. | Pending |

Each criterion requires a dated procedure and redacted actual result. A draft
or static check alone does not pass acceptance.

## 7. Test plan and execution record

Testing is planned, not authorized or run. For prep-005-upgrade-redmine-7-1, verify:
- Success: Pinned digest and versioned source; backup and restore logs; migration and old-tool evidence; no damage to the original 6.0.5 environment.
- Failure: unavailable artifact, rejected permission, malformed response,
  timeout, or failed recovery as applicable; record a blocker.
- Compatibility: compare existing reader catalog and outcomes before/after.
- Synthetic: use the marked isolated environment only after separate authorization.

| Scenario | Criterion | Later verification |
|---|---|---|
| PREP005-001 | AC-001 | Confirm release archive checksum, exact image/platform digests, source container image identity and custom plugin/theme inventory. |
| PREP005-002 | AC-001/002 | Confirm candidate and recovery project, network, volume and localhost port isolation; existing target volumes must be rejected. |
| PREP005-003 | AC-002 | Capture a consistent marked 6.0.5 backup; compare dump listing, row counts and attachment hashes with the original. |
| PREP005-004 | AC-002 | Restore the source snapshot into empty candidate volumes and verify marker, counts and files before migration. |
| PREP005-005 | AC-002/003 | Run explicit 7.0.2 migration; check schema, existing MCP reader catalog, supported Files/Attachments/Issues REST and API-key permission matrix. |
| PREP005-006 | AC-002 | Restore the immutable snapshot into independent 6.0.5 recovery volumes and compare startup, counts, attachments and ordinary-user outcomes. |
| PREP005-007 | AC-003 | Confirm original 6.0.5 container/volume identities and reader outcomes remain unchanged. |
| PREP005-008 | AC-002/003 | Exercise corrupt/incomplete snapshot, nonempty target, permission, transport and failed-recovery paths; retain failures without touching original volumes. |

| Evidence ID | Procedure | Actual result | Status |
|---|---|---|---|
| EVID-001 | `bash scripts/check.sh` in a future coding stage, when applicable | Not run | Pending |
| EVID-002 | `uv run --frozen pytest` only after explicit testing authorization, when applicable | Not run | Pending |
| EVID-003 | Inspector and synthetic procedure only after explicit authorization | Not run | Pending |
| EVID-004 | `bash scripts/doctor.sh`; `uv run --frozen --no-sync ruff check .`; `uv run --frozen --no-sync ruff format --check .`; `uv run --frozen --no-sync mypy src`; `git diff --check` | Prerequisites ready; lint passes; 162 files formatted; no type issues in 79 source files; no whitespace errors | Pass, 2026-10-02 |
| EVID-005 | `docker buildx imagetools inspect redmine:7.0.2-bookworm`; `docker compose --env-file .local/empty-compose.env -f deploy/compose.redmine-7-0-2.yaml config -q` with exported placeholders; `git diff --check` | Official registry index digest resolved; isolated Compose renders with placeholder variables; no whitespace errors | Pass, 2026-10-02 |
| EVID-006 | Download official `redmine-7.0.2.tar.gz` to ignored `.local/`, check published SHA-256, inspect Gemfile/routes/controllers and pinned image entrypoint | Archive checksum passes; source/runtime and 7.0.2 API boundary reviewed without executing the app | Pass, 2026-10-02 |
| EVID-007 | `bash -n` on preparation helpers; `sh -n` on restore helper; render candidate and recovery Compose with placeholder values; `git diff --check` | Shell syntax and both Compose configurations valid; no whitespace errors | Pass, 2026-10-02 |

## 8. Implementation and review record

- Initial planning changes (2026-10-01): this task document only.
- Implementation continuation (2026-10-02): added `docs/redmine-upgrade.md` and linked it
  from operations. Defined artifact/runtime/plugin evidence, isolated project/volume/port
  boundaries, consistent backup, migration, existing-reader and Documents/auth comparison,
  independent source-version recovery, failure handling and evidence retention.
- Retargeting (2026-10-02): user selected 7.0.2 as the maximum supported target.
  Added `deploy/compose.redmine-7-0-2.yaml` with the official image index digest.
  Documents REST is deferred because Redmine dates that API to 7.1.
- Static configuration review: isolated target declares project-scoped database and file
  volumes, reader-only MCP mode, and localhost ports 3001/8001. EVID-005 passed using
  placeholder environment values; no source credentials were read and no services were started.
- Continued implementation (2026-10-02): EVID-006 reviewed exact release and image source.
  Added guarded candidate and recovery preparation helpers, a restore container that accepts
  only a marked 6.0.5 snapshot into empty isolated volumes, and explicit migration controls.
  Pinned the locally cached 6.0.5 recovery and PostgreSQL 16.8 image digests. EVID-007
  covers static syntax and Compose rendering. The source Compose and volumes were not changed.
- Working-tree baseline: existing staged runtime, tests and PREP-004 documentation changes
  were retained. This stage does not alter tests, runtime code or source deployment images.
- Static checks: EVID-004 passes. `scripts/check.sh` was not used; this stage ran the
  allowed static tools directly without installing dependencies or executing tests.
- Earlier diff review: the prior coding stage changed English documentation only.
  Reviewed source-specific helper hazards and retained source configuration, image pins,
  existing staged changes and prior acceptance evidence. No secrets were read or recorded.
- Automated tests: not run.
- Startup, Inspector, and live state checks: not run.
- Remaining coding work: none within PREP-005's implementation scope. The running source
  image identity and extension inventory must be recorded before the rehearsal; if they differ
  from the documented pins, update only the isolated configuration before execution.
- Testing handoff: AC-001 through AC-003, PREP005-001 through PREP005-008 and EVID-002/003
  remain pending. Use the runbook's marked isolated environment, all existing reader operations,
  supported REST/API-key permission matrix, backup integrity, migration/failure recovery and
  source preservation scenarios. Later testing work should cover helper guard/failure behavior
  offline and the opt-in synthetic migration/recovery environment separately.
  Do not carry PREP-004's live waiver forward. No build/dependency changes were needed.

## 9. Completion and handoff

- [ ] Required prerequisite implemented or performed.
- [ ] Acceptance criteria have passing evidence.
- [ ] Authorized verification and applicable static checks pass.
- [ ] Compatibility and recovery/state checks pass where relevant.
- [x] Dashboard and documentation match actual evidence.
- [ ] User accepts this task before the next task starts.

Final status: **implementation finished; testing pending**. Status remains blocked until the
isolated migration, reader/API comparison, recovery and source-preservation evidence passes.
Next action: separately authorize and execute the PREP-005 verification stage in the runbook.
