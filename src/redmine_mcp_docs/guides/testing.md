# Testing and evidence

Testing is described here for a separately authorized verification assignment. Reading these
instructions or serving this portal does not execute tests, prepare fixtures, start Inspector,
or authorize live requests.

## Three layers

| Layer | Location | Purpose and environment |
| --- | --- | --- |
| Unit | `tests/unit/` | Models, policies and services using fake ports |
| Offline integration | `tests/integration/` | REST/MCP contracts with mocked Redmine and internal ASGI |
| Live E2E | `tests/e2e/` | Explicitly selected cases against an isolated, owned Redmine 7.0.2 environment |

Default pytest discovery selects only the two offline layers. Live E2E requires `--run-e2e`,
owned pinned fixtures, and the documented preparation/admission checks. Do not substitute a
shared Redmine instance or a real customer environment.

## Commands for an authorized assignment

Run from Git Bash at the repository root:

```bash
uv run --frozen pytest tests/unit
uv run --frozen pytest tests/integration
uv run --frozen pytest
```

Live preparation creates resources and requires separate authorization:

```bash
uv run --frozen python scripts/prepare-e2e.py
uv run --frozen pytest tests/e2e --run-e2e
```

Consult the [testing roadmap](../docs/testing-roadmap.md) for dependency/fixture prerequisites,
cleanup ownership, supplemental verification, and execution boundaries. Inspector input and
expected results are in [manual verification](../docs/manual-verification.md).

## Interpret existing evidence

Evidence belongs to its recorded revision, environment, scenario set, and date. A historical
passing count does not verify a new working tree or close pending acceptance automatically.

Use the [current task summary](../docs/plans/index.md),
[coverage matrix](../docs/plans/testing-coverage.md), and
[catalog acceptance ledger](../docs/testing/evidence/current-catalog-acceptance.md) together.
Later preparation, retry, and time-entry changes have their own evidence linked from
[Contributors](contributors.md#testing-and-evidence).
Time-entry creation acceptance remains pending, and activity discovery testing was waived in
the documented baseline. Follow the canonical roadmap for subsequent updates.

Coverage thresholds, testing CI, and broader operational/recovery readiness remain deferred.
The portal preserves the existing evidence rather than presenting a new acceptance result.

## Verify the portal separately

The [portal checklist](verification.md) covers offline assets, navigation, diagrams, export
boundaries, and static deployment. It needs no Redmine credentials or test fixtures. The
implementation handoff does not claim those manual checks were performed.
