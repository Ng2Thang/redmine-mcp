# Code-quality remediation backlog

Status: audit tooling implemented; initial static audit completed on 2026-10-15 with findings.
Runtime remediation and functional verification are not complete.

Current source scan/fix scope is `src/redmine_mcp/` only, as clarified by the user. Support
scripts, seed tools and documentation code are excluded. The original findings remain dated
evidence; exclusion is not remediation or a security waiver.

The [reviewed audit](../reports/code-quality-audit.md) owns evidence, finding locations,
triage and limitations. The [audit workflow](../code-quality.md) owns repeatable commands.
This backlog proposes focused follow-up patches; no automatic rewrite or blanket suppression
is authorized by a scanner's recommendation.

## Work items

| ID | Priority | Scope / finding | Deliverable | Status |
|---|---|---|---|---|
| CQ-R01 | P2 | Documentation tooling typing, CQ-01 | Correct all 4 recorded strict mypy errors without weakening configuration | Outside current scope |
| CQ-R02 | P2 | Capability discovery, CQ-03 | Extract role-evidence/tool-assembly helpers and preserve visibility/pagination contracts | Pending |
| CQ-R03 | P2 | Mutation transport/writers, CQ-04 | Review responsibilities; isolate status/payload handling only where behavior stays explicit | Pending |
| CQ-R04 | P2 | Async helper startup, CQ-05 | Review process creation, cancellation, hidden windows and cleanup; apply a focused correction if warranted | Outside current scope |
| CQ-R05 | P2 | Support security candidates, SEC-02 | Review all argv/executable/PATH boundaries and assertion assumptions; document per-call dispositions | Outside current scope |
| CQ-R06 | P3 | Runtime baseline convention, CQ-02 | Runtime Ruff/format gate passed on 2026-10-15; retain broader original counts as historical | Runtime static gate passed |
| CQ-R07 | P3 | Supplemental conventions, CQ-06 | Decide applicable rules; fix small coherent groups and document justified exceptions | Pending |
| CQ-R08 | P3 | Remaining runtime complexity/MI signals, CQ-06 | Review runtime hotspots; support/runner metrics are outside current scope | Pending |
| CQ-R09 | Follow-up | Uncovered languages/duplication | Scope Bash/Ruby/JS, duplication and container checks only if requested | Deferred |

No confirmed high-severity vulnerability was established; priorities above reflect the
observed quality gaps. New evidence can change their order. CQ-R06 is a small independent
patch and can precede refactoring. CQ-R07/CQ-R08 depend on triaging overlap with CQ-R02/CQ-R03
so the same code is not repeatedly rewritten. Runtime dependency upgrades are not proposed
solely because the advisory database could change later.

## Acceptance and handoff

- CQ-R01 (outside current scope): `uv run --frozen mypy src/redmine_mcp_docs` passes. Review source contracts and preserve documentation
  export/serving behavior; runtime verification requires separate authorization.
- CQ-R06: affected baseline Ruff and formatter checks pass. Review the diff for formatting
  and import-only changes; preserve operation IDs, public schemas and writer gates.
- CQ-R02/CQ-R03: document the specific responsibility being extracted, before/after contract,
  risk-sensitive branches and relevant existing verification scenarios before editing.
  Static checks alone do not establish behavior preservation.
- CQ-R04: preserve Windows hidden subprocess startup, log ownership, cleanup and cancellation.
  Do not execute the Inspector helper as part of static cleanup.
- CQ-R05/CQ-R07: every exception names a finding, source location, reason and re-review
  condition; no blanket ignores or silent removal from scanner scope.
- CQ-R08: prioritize cohesive responsibilities and measured problems. Complexity/MI numbers
  are review signals; no requirement to force every score below a threshold.

After a focused patch, rerun affected static analyzers and produce a new dated evidence
directory. Compare findings by file/position/rule rather than summing overlapping tools.
The audit wrapper exits 1 for findings/review signals and 2 for incomplete analysis.
Evaluate the current runtime baseline using fresh runtime-only evidence. Do not claim the
original broader baseline passes merely because support/documentation findings were excluded.

No test dependencies, fixtures or test code were added for this audit. For subsequent behavior
changes, identify relevant existing tests and uncovered scenarios, then hand off execution
separately under the [testing roadmap](../testing-roadmap.md) and
[coverage plan](testing-coverage.md). Unit, integration, E2E, application startup, Inspector,
Docker operations and live Redmine mutations require a separately authorized assignment.
