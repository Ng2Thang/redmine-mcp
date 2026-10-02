# Isolated Redmine 7.0.2 upgrade and recovery

This runbook belongs to [PREP-005](plans/tasks/prep-005-upgrade-redmine-7-1.md).
It prepares a future rehearsal; no migration or recovery has been performed.
Execution requires a separate verification assignment.

## Release and image pin

Checked on 2026-10-02: the official [download page](https://www.redmine.org/projects/redmine/wiki/Download)
lists 7.0.2. The [official Docker image](https://hub.docker.com/_/redmine)
publishes `7.0.2-bookworm`. A read-only registry manifest inspection resolved the
multi-platform index digest `sha256:5cb12288dbfb807f136adbee02d60a96acc24edad0404cbfce214a7ced39ff6a`.
The Linux amd64 child digest is
`sha256:b71640b748bb26314b559e04f640c3f0e7199ba0540d62a22767776a335f8e2d`.
[The isolated Compose target](../deploy/compose.redmine-7-0-2.yaml) pins the index digest.
This identifies the image; it does not prove the upgrade works. The official
7.0.2 source archive was downloaded into ignored `.local/` and verified against
the published tarball SHA-256 on 2026-10-02.

Before running the rehearsal, record the following in the task evidence:

| Item | Required evidence |
|---|---|
| Release | Exact 7.0.2 archive URL and SHA-256; official download lists SHA-256 `d45e6d4c373cc3c8d33f1f4d4a2ffae1e1adb18703160707467493de7b4be591` for the tarball |
| Source | Release tag/revision and immutable source URL matching the archive |
| Image | Official `7.0.2-bookworm` tag, index digest above, selected OS and architecture |
| Runtime | Versioned Ruby, Rails, database and gem requirements; compatibility with PostgreSQL 16.8 |
| Extensions | Installed plugin/theme names, versions, checksums and target compatibility, or observed absence |
| Image behavior | Matching Dockerfile and entrypoint revision, including automatic migration behavior |
| API | Versioned Files, Attachments, Issues and API-key authentication behavior; Documents REST is unavailable in 7.0.2 |

The verified 7.0.2 `Gemfile` requires Ruby 3.2 through 4.0 and Rails 8.1.4;
the selected [Dockerfile](https://github.com/docker-library/redmine/blob/df0d3284a3da8a77363a086cecba5eeed7f4f1f9/7.0/bookworm/Dockerfile)
uses Ruby 4.0 and embeds the same SHA-256 verified release archive. The
[Redmine installation requirements](https://www.redmine.org/projects/redmine/wiki/RedmineInstall)
recommend PostgreSQL 14 or later for 7.0, so the existing 16.8 server satisfies
the documented minimum. The image's
[entrypoint](https://github.com/docker-library/redmine/blob/df0d3284a3da8a77363a086cecba5eeed7f4f1f9/docker-entrypoint.sh)
automatically runs `db:migrate` before a normal server start unless
`REDMINE_NO_DB_MIGRATE` is set. The candidate Compose sets that flag and requires
an explicit migration command. It does not mount custom plugins or themes;
inspect the original runtime for extensions before executing the upgrade.

In the verified 7.0.2 source, `DocumentsController` renders and redirects HTML
without an API response branch. `EnumerationsController#index` accepts API
authentication and responds in API format, so document category enumeration can
remain in the 7.0.2 reader roadmap. The supported Files/Attachments/Issues
contracts still need their own task-level review and runtime acceptance.

Confirm the pinned index still contains the selected platform manifest before execution.
Keep the source PostgreSQL version fixed during the Redmine rehearsal.
If that database version is unsupported, define a separate database migration before proceeding.

## Isolation contract

The original project is `redmine-mcp-test`, with Redmine `6.0.5-bookworm`, PostgreSQL
`16.8-bookworm`, and host ports 3000, 8000 and 5433. Preserve its volumes and configuration.

Use the checked-in isolated Compose target with a private environment file under ignored
`.local/upgrades/<rehearsal-id>/`. The preparation helpers fix the candidate project to
`redmine-mcp-7-0-2` and the recovery project to `redmine-mcp-recovery-6-0-5`.
Review the rendered configuration privately before execution:

- Use fresh, project-scoped database and attachment volumes and networks. Do not use external
  volumes, explicit source volume names, or the source PostgreSQL host.
- Bind rehearsal ports to localhost: Redmine 3001 and MCP 8001. PostgreSQL is not
  published. Use distinct unused localhost ports for recovery.
- Mount only rehearsal-owned state directories. Do not mount the source `.local` directory
  writable, the seeding directory, or source attachments into either candidate project.
- Keep MCP writes disabled and use the same ordinary personal reader identities for comparisons.
  Disable outbound mail, webhooks, scheduled jobs and integrations in the copy before app startup.
- Confirm the synthetic marker in source configuration and snapshot, and inspect resolved
  project/container/volume names before any restore or migration. Fail on any source overlap.

Do not reuse `scripts/common.sh`, `restore.sh`, `reset-test-env.sh` or `dev-up.sh` for the copy.
Those wrappers select `redmine-mcp-test`; restore replaces its database and files. A different
Compose project name alone also leaves inherited published ports and bind mounts unchanged.
The [candidate](../scripts/prepare-upgrade-copy.sh) and
[recovery](../scripts/prepare-recovery-copy.sh) helpers reject existing target
volumes and copy the trusted source snapshot before any restore. The
[restore container](../tools/upgrade/restore-copy.sh) mounts that copy read-only,
requires a marked 6.0.5 snapshot and an empty target database and files volume,
and leaves failures in isolated resources for diagnosis. Do not start the candidate
or recovery Redmine service before restore.

## Consistent backup and baseline

During the authorized verification stage, capture existing catalog names, schemas, annotations,
and ordinary-user outcomes using [the tool reference](tool-reference.md) and
[manual verification](manual-verification.md). Include project/issue IDs, visibility decisions,
journals, transitions, categories, versions, dates/hours, entries and user memberships.
Record empty results explicitly; retain PREP-004's waived live gaps as limitations.

Choose an unused snapshot ID. The existing source backup command is:

```bash
bash scripts/backup.sh prep005-preupgrade-YYYYMMDD
```

It temporarily stops source Redmine and MCP and attempts to restart them on exit. Schedule this
interruption explicitly for the verification stage. Inspect the actual result; a restart attempt
does not prove service recovery. Never run the source restore helper for this rehearsal.

Require a completed snapshot with database dump, attachment archive, marker, manifests,
credentials and image metadata. Save hashes, source image digests, volume identities, schema
migration versions, row counts and attachment checksums privately. Validate the dump listing
and archive paths; reject incomplete, mismatched, corrupt or unsafe archives before import.
The candidate preparation helper copies the snapshot into rehearsal-owned storage
and keeps the pre-upgrade original immutable.
Snapshots contain secrets and must remain ignored and absent from shared logs.

## Copy, migrate and compare

1. Run `bash scripts/prepare-upgrade-copy.sh SNAPSHOT_ID` only in the authorized
   verification stage. It creates fresh isolated PostgreSQL and attachment volumes
   and restores the 6.0.5 snapshot there. The helper checks the database marker;
   compare isolated row counts and attachment hashes with the original baseline
   before migration. Ordinary-user baseline outcomes come from the original instance.
   If restoration fails, leave the isolated applications stopped and retain failure evidence.
2. Record database and attachment hashes of the validated isolated copy before
   migration. The candidate image's automatic migration is disabled by default.
3. Follow the release-specific [upgrade guide](https://www.redmine.org/projects/redmine/wiki/RedmineUpgrade).
   Use an explicit `rake db:migrate` in the candidate project, then clear cache.
   Run plugin migration only if the runtime inventory finds compatible custom plugins.
   Capture exit codes and sanitized logs. Do not copy old `config/settings.yml`
   over the new release or run migrations twice.
4. Confirm actual Redmine/Ruby/Rails/database versions and completed schema migrations. Start
   candidate MCP against candidate Redmine only, with writes disabled.
5. Compare every existing reader operation and MCP discovery/invocation/error outcome against
   the baseline with the same ordinary identities. Verify API-key auth, missing/rejected keys,
   restricted resources, pagination, empty collections and populated collections.
6. Confirm the scoped Files, Attachments and Issues REST endpoints against 7.0.2 source and
   ordinary-user permissions. Do not expose Document MCP tools: the
   [Redmine REST index](https://www.redmine.org/projects/redmine/wiki/Rest_api) dates
   Documents REST to 7.1.

Run the following only in the separately authorized verification stage. Use
the actual snapshot ID throughout. Stop after preparing the copy and compare
its database counts and attachment hashes with the original baseline before
issuing the migration command:

```bash
snapshot_id=prep005-preupgrade-YYYYMMDD
bash scripts/prepare-upgrade-copy.sh "$snapshot_id"
```

Once the isolated copy is validated, migrate and start the candidate:

```bash
docker compose -p redmine-mcp-7-0-2 --env-file ".local/upgrades/$snapshot_id/candidate.env" -f deploy/compose.redmine-7-0-2.yaml run --rm redmine rake db:migrate
docker compose -p redmine-mcp-7-0-2 --env-file ".local/upgrades/$snapshot_id/candidate.env" -f deploy/compose.redmine-7-0-2.yaml run --rm redmine rake tmp:cache:clear
docker compose -p redmine-mcp-7-0-2 --env-file ".local/upgrades/$snapshot_id/candidate.env" -f deploy/compose.redmine-7-0-2.yaml up -d --wait redmine mcp-server
```

## Recovery and acceptance handoff

Restore the immutable pre-upgrade backup into fresh volumes in the separate recovery project,
using `bash scripts/prepare-recovery-copy.sh SNAPSHOT_ID`. The recovery Compose
pins the locally cached 6.0.5 image digest
`sha256:3490ba81408371d8e2d17c96223ed028b3739e7fc2eb8116287b4e011f2797b3`.
Candidate, restore and recovery services also pin the locally cached PostgreSQL
16.8 index digest
`sha256:301bcb60b8a3ee4ab7e147932723e3abd1cef53516ce5210b39fd9fe5e3602ae`.
Before running recovery, compare this pin with the actual source container image
identity; a mismatch blocks rehearsal until the correct source image is pinned.
Validate source-version startup, schema versions,
record counts, attachment checksums, marker and baseline reader/auth outcomes. Pointing the
old image at a migrated database is not recovery. Preserve a failed candidate for diagnosis;
never repair or replace the original instance to recover the copy.

The independent recovery stage uses the same immutable snapshot copy and its
private environment file:

```bash
bash scripts/prepare-recovery-copy.sh "$snapshot_id"
docker compose -p redmine-mcp-recovery-6-0-5 --env-file ".local/upgrades/$snapshot_id/candidate.env" -f deploy/compose.redmine-6-0-5-recovery.yaml up -d --wait redmine mcp-server
```

After rehearsal, confirm the original source volume identities, image versions and baseline
outcomes still match. Cleanup may remove only the recorded candidate/recovery resources after
evidence has been retained. Do not use the source reset helper or delete the source volumes.

The later verification assignment must record dated, redacted results for AC-001 through AC-003:
artifact/source/digest validation; isolation rejection; backup integrity; successful copy and
migration; every reader contract; Files/Attachments/Issues and API-key permissions; unavailable artifact, malformed
response, timeout and failed-recovery handling; successful independent recovery; and original
instance preservation. No scenario passes merely because this runbook exists.
