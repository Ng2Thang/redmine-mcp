# Issues task-plan self-review

## Scope and provenance

Initial source-based self-review on 2026-09-29 of analysis/index and tasks issues-000 through
issues-008 against the full original issues.md, current code, workflow and nine-section template.
Target Redmine 6.0.5-bookworm. Source SHA256 and baseline HEAD are in analysis.md.
This is task-plan readiness review, not independent review, code correctness or acceptance.

## Findings

| Finding | Severity | References | Evidence and impact | Required correction | Resolution |
|---|---|---|---|---|---|
| REV-001 | major | All task sections 6-7 | Generic Given/When/Then rows are not directly mapped to named scenarios; prerequisites include irrelevant runtime expectations | Make criteria concrete and map scenarios; mark policy runtime tests N/A | Open at initial review |
| REV-002 | major | issues-002-write-access; deploy/compose.yaml | New environment setting is not forwarded by Compose; separate writer requires different localhost port | Specify Compose forwarding and configurable port preserving 8000 default, document deployment isolation | Open at initial review |
| REV-003 | blocking | issues-005 through issues-008, SRC-013-019 | Target watcher permission/success, update clearing/private-note, API success renderer and upload token evidence incomplete | Obtain named versioned evidence and finalize contracts before coding | Open; evidence blocker, not assumed support |
| REV-004 | blocking | Workflow shared prerequisite; issues-001; dependent feature tasks | Mandatory test baseline absent, explicitly excluded from coding skill | Separate testing assignment must establish baseline before dependent feature coding | Open; execution prerequisite |

## Coverage and readiness

All SRC-ISSUES-001 through 020 were reconciled against original source headings/fields.
Existing basic reads preserved. List covers extra IDs, subprojects, custom/date filters, sort,
includes and common fields; detail covers seven supported includes and upstream workflow/visibility.
Reactions are deferred for target incompatibility; XML is an upstream alternative, not a new MCP
format. Attachments on writes remain explicitly blocked on token evidence; linked uploader is
outside issue-resource implementation. Writes and watcher pair have named contract blockers.

Task IDs/links and dependencies are unique and acyclic; list owns common model additions, detail
depends on list, writes depend on detail/create common contracts. No task is marked complete.
Owner-selected separate writer deployment resolves product authorization choice; credentials and
synthetic permissions remain verification/setup prerequisites.

Initial verdict: changes required for policy/access/read task planning (REV-001/002); blocked
for whole-feature readiness (REV-003/004). Correct actionable planning defects using planning
skill, then re-review once. No tests or live verification performed.

## Revision and re-review round 1

Planning skill corrected scenario/criterion references in every task and marked policy runtime
tests N/A (REV-001). Access task now explicitly owns Compose flag/host-port forwarding and
private-env/project separation (REV-002). Review skill was re-read; corrected contracts were
compared with original source, dependency owners, actual config/security/Compose code and template.
No new API claims, evidence, or dependency cycles introduced. Initial findings above are retained;
REV-001 and REV-002 are resolved by those saved corrections. REV-003/004 remain open.

| Task | Final planning readiness | Coding disposition |
|---|---|---|
| issues-000-policy | ready | Assign documentation coding now |
| issues-001-testing-baseline | ready plan | Excluded, separate testing executor needed |
| issues-002-write-access | ready for runtime/config portion | Assign after policy coding; synthetic setup remains separate |
| issues-003-list, issues-004-detail | ready plan | Blocked by required baseline dependency |
| issues-005-create through issues-008-watchers | blocked | Resolve named target evidence and prerequisite implementation |

Final overall verdict: blocked. One correction/re-review cycle used; no second cycle needed
for known defects that require excluded work/evidence. This does not approve unresolved writes.

Reviewed task SHA256 hashes before coding:
- issues-000-policy.md: `2C535F25E68DCAA222905FD404070B0F6738CAE73EE455ACC7A5D8BBED16B98A`
- issues-001-testing-baseline.md: `74057D94F7BBA0B38F1CD5E39E4060E06BAC5F9337F3CDBEC07C42103D06BB90`
- issues-002-write-access.md: `D52A0996337556DDD619A513BCDB4A4FCC24665D9E4040BE0CB0C463B7A818EA`
- issues-003-list.md: `9A06A227BA024036652F93BC993CFE60FE7A95A3F10D4D31A9D3E05A93B1A13F`
- issues-004-detail.md: `76026DB448ACED19F6267F7CE334635CA7E2F5B9C07798DA764E9BF53F00BF7D`
- issues-005-create.md: `8A370F4EC8B6D05ADC4BFA976AF3FE13524D44F871AB1BC5D9D6C142E7C140D6`
- issues-006-update.md: `B1F0D754492CBF654B3905270565BE91348B432292B870B63FBD58D01876DFB7`
- issues-007-delete.md: `DB464BE3283C724C3171B043C352F522DE509D39AA94F8BF439F56DFCB378328`
- issues-008-watchers.md: `1FAD69064E0028E02528CB72C683BE9C8B5B8199B3955F14BE27191ABE210354`

## Coding handoff

Within this requirement assignment explicitly assign issues-000-policy, then the runtime gate/
configuration portion of issues-002-write-access to the implementation skill. This does not
declare their acceptance or the whole shared prerequisite complete. Defer issues-001 to testing;
feature tasks await foundation and contract readiness. Preserve every acceptance scenario.

## Execution handoff update

Policy and runtime gate/configuration coding portions finished; their task records retain
status blocked for static environment/acceptance. No feature read extensions or mutations were
coded. Static checks attempted in sandbox (Bash shared-memory access failure) and then via
authorized escalation with no-sync/offline/downloads disabled. Bash launched, but each uv
invocation stopped before Ruff/mypy because Python 3.13 is absent; no source check passed.
Tracked git diff --check passed. Individual untracked planning-file whitespace inspection
initially found trailing blank lines; these were removed and all file checks then passed.
No tests, dependencies, fixtures, startup, MCP Inspector, builds or live verification ran.

Exact next action: supply Python 3.13 with installed static tools and repeat recorded commands;
separately assign issues-001-testing-baseline, ACCESS-001/002/003 and restricted synthetic writer
setup. Resolve REV-003 versioned contracts before coding the affected mutation tasks, then resume
the dependency-ordered feature backlog. Required acceptance evidence remains pending.
