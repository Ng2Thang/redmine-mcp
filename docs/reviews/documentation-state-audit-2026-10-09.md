# Documentation state and release preparation audit

> Writer admission update (2026-10-13): pinned-key and user ID admission checks
> are retired. Earlier requirements and evidence below describe historical behavior.
> See [current configuration](../configuration.md#separate-writer-deployment).

Date: 2026-10-09.

## Scope and method

This audit compares the main contributor and user guides with the current working tree,
tracked configuration, source code, Git history, roadmap and recorded verification evidence.
The inspected HEAD is `e6ad1e0`. Two pre-existing unstaged changes are present in
`src/redmine_mcp/integrations/redmine/write.py` and `tests/e2e/test_live_acceptance.py`.
They were read and preserved.

Review used file reads, text searches and Git inspection only. No tests, lint/type/architecture
checks, dependency installation, builds, startup, Inspector, live calls, deployments or recovery
commands were executed. Historical results below are repository records, not new verification.
During the initial audit, existing guides and runtime files were not edited; this report was
the only added file. The subsequent user-requested Markdown corrections are recorded below.

The audit covers the principal guides and selected supporting tasks/evidence. It is not a
line-by-line review of every historical task, nor an automated check of every Markdown link.

## Current source baseline

| Area | Observed state | Source |
|---|---|---|
| Runtime | Python 3.13; FastAPI REST routes reused by MCP | [Metadata](../../pyproject.toml), [app](../../src/redmine_mcp/app.py) |
| Read catalog | 18 registered operations | [MCP catalog](../../src/redmine_mcp/mcp/catalog.py) |
| Write catalog | 18 registered operations, gated by writer configuration and authorization | [Policy](../../src/redmine_mcp/auth/policy.py), [settings](../../src/redmine_mcp/config.py) |
| Default deployment | Reader on localhost:8000; opt-in writer on localhost:8001 | [Compose](../../deploy/compose.yaml) |
| Target environment | Synthetic Redmine 7.0.2 image pinned by digest | [Synthetic Compose](../../deploy/compose.test.yaml) |
| MCP compatibility | FastAPI-MCP 0.4.0 and MCP SDK 1.30.0 pinned | [Metadata](../../pyproject.toml), [compatibility](../../src/redmine_mcp/mcp/compatibility.py) |
| Quality script | Ruff lint, Ruff format check, mypy and an architecture check | [Script](../../scripts/check.sh) |
| Test discovery | Unit and integration by default; live E2E requires explicit selection | [Metadata](../../pyproject.toml), [test setup](../../tests/conftest.py) |
| Version | Package and FastAPI app both use 0.1.0; changelog remains Unreleased | [Metadata](../../pyproject.toml), [app](../../src/redmine_mcp/app.py), [changelog](../../CHANGELOG.md) |

## Initial documentation discrepancies

The locations and wording below describe the files before the subsequent corrections.

| Priority | Location | Finding and needed correction |
|---|---|---|
| High | [AGENTS.md](../../AGENTS.md), lines 67-70 | Says current tools remain read-only and issue writes are future work. Current source implements 18 writes. Describe the default reader as read-only and the separate writer as implemented, with pinned-key or personal-key authentication, operation gates and native permissions. The legacy key/token wording should match the personal API-key contract. |
| High | [Operations](../operations.md), line 154; [development](../development.md), line 185 | Both still say 15 writes/mutations. The current registered total is 18. Keep historical 15-write evidence unchanged, but update these present-tense deployment instructions. |
| High | [MCP request flow](../mcp-request-flow.md), line 223 | Says there is no retry loop. Shared GET retries are implemented by PREP-027. Explain bounded eligible GET retries and preserve the single-attempt mutation rule. The normal three-request get_issue example describes the first-attempt success path; transient failures can add physical attempts. |
| High | [MCP request flow](../mcp-request-flow.md), line 34 | Says discovery does not fetch project or issue data. Personal-key writer discovery can inventory visible projects and read role/capability evidence. Scope the static-discovery statement to the reader/pinned-key catalog and describe personal-key discovery separately. |
| Medium | [Tool reference](../tool-reference.md), lines 39, 60 and 132; [configuration](../configuration.md), lines 76 and 137; [architecture](../architecture.md), line 67; [MCP request flow](../mcp-request-flow.md), line 21 | Still describe PREP-022, 023, 024, 025 or 026 runtime acceptance as pending. The [2026-10-07 preparation record](../testing/evidence/prep-022-026-testing.md) accepts their defined functional scope, including 1,395 offline and 23 owned live cases. Replace current pending claims with links to that evidence and retain its limitations. |
| Medium | [Development](../development.md), lines 47-48 | Says check.sh runs all three checks. It now runs four, including scripts/check_architecture.py. The optional pre-commit configuration still has three hooks; do not claim the hooks also run the architecture check. |
| Medium | Repository `AGENTS.md`, lines 8-9; [tool workflow](../workflows/redmine-tools.md), runtime architecture section | Blanket FastAPI import prohibition conflicts with the documented and implemented narrow exception for `from fastapi import status as http_status`. Align the instruction with [architecture](../architecture.md) and the [architecture checker source](../../scripts/check_architecture.py); framework APIs and HTTPX remain outside service contracts. |
| Low | Repository `AGENTS.md`, lines 60-61 | The no-existing-commits wording no longer reflects this repository's history. Git history includes feat:, sup:, updt: and opt: subjects. State the intended contributor convention directly without suggesting the repository has no history. |

## Configuration and release metadata gaps

- `REDMINE_MAX_REQUEST_BODY_BYTES` exists in Settings and is documented, but neither MCP
  service in `deploy/compose.yaml` forwards it. Supplying it only in a Compose interpolation
  env-file therefore does not configure the container. The derived default still applies.
  Document the local/Compose distinction or explicitly implement forwarding in a separate
  configuration change. The guide already notes that PREP-024 did not change Compose; keep
  that historical fact while making the actual operator behavior explicit.
- `pyproject.toml` still describes the package as "Read-only Redmine tools over FastAPI MCP".
  That description omits the implemented writer. It also declares no project readme or project
  URLs. Review distribution metadata before packaging a public release.
- No license file, release tag or `.github` workflow is tracked in the inspected checkout.
  Decide public distribution terms and the release process. CI is already explicitly deferred
  in the guides, so its absence is a release preparation decision rather than a false doc claim.
  Remote releases, branch protections and private reporting settings were not inspected.
- SECURITY.md and CODE_OF_CONDUCT.md openly state that no dedicated private reporting address
  is published. Provide a concrete maintained contact for a public release if one is available.

## Accurate guidance and evidence boundaries

README.md and the tool reference correctly identify 18 reads and 18 writes. Reader/writer
separation, personal API keys, localhost ports, the pinned target and Unreleased status align
with source. SECURITY.md accurately distinguishes functional evidence from production readiness.

The 2026-10-07 PREP-020 ledger covers its dated 17-read/15-write catalog. Its 1,086 offline and
21 live results should not be renamed or presented as a fresh verification of today's catalog.
CONTRIBUTING.md explicitly attributes those counts to that dated ledger; this is historical
evidence, not a wrong current catalog count.

The [TOOL-043 record](../testing/evidence/tool-043-testing.md) reports a later clean full offline
run with 1,889 passes and 12 owned native cases across two executions. TOOL-042 has its own
[record](../testing/evidence/tool-042-testing.md). These do not establish that the current dirty
working tree was verified, or automatically close every earlier acceptance gap.

The roadmap appends planning, coding and testing events. Earlier paragraphs saying TOOL-043
is planned or that the catalog has 17 writes are followed by later implementation/acceptance
entries. Preserve that history, but add a concise current-status summary so readers do not
mistake earlier stage statements for current state. Historical task blockers and waivers must
not be silently changed to passed acceptance.

## Open release decisions and acceptance

| Area | Recorded state | Release action |
|---|---|---|
| TOOL-040 activity discovery | Implemented; testing explicitly waived | Disclose the waiver; authorize verification separately if required for the release |
| TOOL-041 own-time creation | Implemented; defined acceptance remains pending | Complete its assigned acceptance or explicitly disclose/exclude this capability in release scope |
| RedmineUP tags | Selected filtering evidence uses Redmine 6.0.5; 7.0.2 overlap/private-role acceptance remains pending | Establish target-version acceptance before promising that plugin/version combination |
| PREP-028 detail-tag mapping | Implementation finished; task acceptance pending | Reconcile its specific scenarios independently from filter evidence |
| BUG-001 get_issue | Roadmap still records a blocked investigation requiring failing sanitized upstream data/arguments | Triage relevance to the release; do not silently mark it resolved |
| Packaging | Build command exists; isolated distribution acceptance remains deferred | Build and verify the selected source/wheel or container artifacts within an authorized stage |
| Recovery/operations | Full restore, checksum/failure recovery and operational acceptance remain deferred | Required work for a production claim; disclose limits for a pilot |
| Final release review | PREP-009 remains blocked and scoped to an older roadmap | Reconcile final acceptance against the present catalog and exact release revision |

## Suggested release sequence

1. Choose pilot/prerelease or production scope, target Redmine/plugin support and artifacts to
   distribute. Current documentation describes a pilot implementation.
2. Correct the current-guidance discrepancies above and publish a concise current capability
   and evidence summary. Preserve dated task/evidence history.
3. Resolve metadata, version, changelog, reporting contact and distribution terms. Keep package
   metadata, FastAPI version, lock metadata where applicable, tag and release notes consistent.
4. Review the two pre-existing changes and select a clean exact release revision. Resolve the
   open feature/bug decisions and record included capabilities, waivers and limitations.
5. In a separately authorized verification stage, run the documented static checks, relevant
   offline tests and owned 7.0.2 REST/MCP/Inspector checks. Review artifact installation and
   container behavior. Record actual results tied to the final revision, not only older totals.
6. For production scope, also complete operational, recovery, deployment/rollback and permission
   acceptance. For a pilot, explicitly state outstanding limits and support expectations.
7. Complete the refreshed PREP-009 release review, then create the version tag and publish the
   reviewed artifacts and release notes through the selected distribution process.

The steps above are a checklist, not execution authorization. No release has been created or
published by this audit.

## Markdown corrections (2026-10-09)

The user subsequently requested correction of the Markdown documentation. The following
changes address the initial findings without changing runtime code, configuration or tests.

| Finding | Correction |
|---|---|
| Reader/writer and stale write counts | AGENTS.md, development and operations now describe the 18-read/18-write catalog and the separate authorized writer |
| FastAPI import instructions | AGENTS.md, CONTRIBUTING.md, development and the tool workflow now preserve the narrow HTTP status constants exception |
| Commit-history wording | AGENTS.md states the intended commit convention directly |
| Quality script versus hooks | Development documents four script checks and three optional hooks; the equivalent command list includes the architecture checker |
| GET retry and discovery | MCP request flow documents bounded GET retry, single-attempt mutations, personal-key capability discovery and the first-attempt success assumption in its request count |
| PREP-022–026 acceptance | Tool reference, configuration, architecture and request flow link the accepted functional record and retain its limits |
| Compose body-cap distinction | Configuration explicitly explains local settings, absent base Compose forwarding and the derived container cap |
| Current state versus history | Roadmap has a dated current-status summary; README, contributor/manual/testing guidance identify the PREP-020 catalog as historical and point to later evidence |
| Change record | CHANGELOG.md records the Markdown correction under Unreleased |

Review consisted of reading the edited passages and Git diffs. No tests, lint/type/architecture
checks, build, dependency installation, startup, Inspector or live operations were performed.
The pre-existing runtime/test edits were preserved. Historical evidence and task acceptance
records were not rewritten; TOOL-040's waiver and the remaining feature, bug, release and
operational gaps remain open as previously recorded.

Non-Markdown work remains separate: package metadata, optional Compose setting forwarding,
distribution terms/reporting contacts, CI, final revision verification and release publication.
The initial metadata/deployment findings above remain relevant; this correction does not claim
they were implemented or tested.
