# G03: Older writer scenario coverage

Date: 2026-10-14. Status: complete within the defined offline scope; full regression passed.

## Assignment and source

The user assigned G03 from the [coverage plan](../../plans/testing-gap-plan-2026-10-14.md).
This work adds independent verification and REST/MCP scenarios for issue creation/copy/update,
journal edits, relations, watchers and attachment updates/deletion. It also corrects the
shared synthetic fixture's production-derived relation response and hardcoded watcher target.

Base revision: `2938733394a72ddf0fcfda7632a7a93bdd47a41f`, plus the earlier G02 test additions,
the G03 files below, changes to `tests/integration/conftest.py` and documentation updates.
The pre-existing README and documentation changes were preserved. Runtime code, public
contracts, dependency pins, setup helpers and native Ruby scripts were not changed.

Private logs and machine-readable results are retained in
`.local/testing/g03-2026-10-14/`. The tested source manifest includes tracked source/configuration,
the modified integration fixture and the new G02/G03 files. Its hash is:

```text
4b84c825768b3803c4761a30289ccfeb76c1bf0d223b5ff60d4bf09aee253556
```

All manifest hashes still matched after the complete run. No tested source changed while
the final evidence and roadmap documentation were updated.

The locked Python/pytest environment remains the G01/G02 environment.
`bash scripts/doctor.sh` passed. Its optional tool-version checks did not start or mutate
Docker stacks. Git Bash required an outside-sandbox launch because Windows denies its
shared-memory initialization inside the sandbox.

## Cases and independent expectations

The G03 additions contain **318 cases: 66 unit and 252 integration**.
`tests/issue_write_helpers.py` owns literal native relation results and shared invocation/
override helpers; it is not a collected test module.

| Owner | Cases | Plan mapping | Behavior |
| --- | ---: | --- | --- |
| `tests/unit/test_issue_relation_normalization.py` | 24 | WRT-01 | Nine supported types in both endpoint orders, inverse direction, scheduling defaults and signed/zero delays |
| `tests/unit/test_issue_write_verification.py` | 42 | WRT-06 | Custom-field scalar/list/null/presence, upload identity/metadata, optional references, watcher sets, verification precedence and unambiguous new caller-journal attribution |
| `tests/integration/test_issue_relations.py` | 80 | WRT-01/02/07 | Exact original payload, literal normalized read-back, self-link rejection, invalid endpoint proofs, independent post-delete observations and unusable receipt/field presence |
| `tests/integration/test_issue_notes.py` | 32 | WRT-04 | Same-journal membership, missing/duplicate/malformed/other-issue targets, exact empty/privacy payloads, hidden/ignored read-back and native privacy rejection |
| `tests/integration/test_issue_watchers.py` | 32 | WRT-05 | Target user 8 with control user 3, existing/absent no-ops, omitted/empty/duplicate/malformed/forbidden/opposite membership observations |
| `tests/integration/test_attachment_write_boundaries.py` | 50 | WRT-03 | Project/version/issue membership proofs, wrong containers/projects/versions, malformed lists, exact writes, preserved control and unavailable/mismatching read-back |
| `tests/integration/test_issue_write_variants.py` | 58 | WRT-06/07 | Create/copy/update optional fields, explicit clearing versus omission, exact copy query, ignored/hidden fields, unusable 201 identities, failed read-back and committed lost replies |

Relation fixtures are literal expectations independently checked against
[Redmine 7.0.2 IssueRelation](https://raw.githubusercontent.com/redmine/redmine/7.0.2/app/models/issue_relation.rb).
They cover canonical/inverse directions, symmetric ID ordering and scheduling delay handling.
Neither the shared fake nor the fixture table calls production `expected_relation`.
Changing the production normalization can therefore cause the matched-receipt assertions
to fail instead of changing both sides of the expected result.

The shared fake now reads watcher IDs from the native `watcher.user_id` payload and DELETE
path, preserves other watchers, and removes only attachment 9 from its file/issue lists.
The shared writer success/error matrix remains in place.

Assertions distinguish accepted/uncertain receipts from matched/mismatch/unavailable state.
Missing watcher expansions cannot prove absence; empty expansions can. Missing notes or
hidden journals cannot prove clearing. An unusable creation ID cannot trigger subject/list
reconciliation or another mutation. Attachment metadata alone cannot prove container membership.
Pure helper expectations are authored directly; native response fixtures do not call the
verification helper being exercised.

## Execution and corrections

| Stage | Result | Duration | Local log |
| --- | --- | --- | --- |
| First relation/unit run | 144 passed, 2 failed | 65.50 seconds | `relations-first.log` |
| First complete new-case run, before late clear cases | 248 passed, 62 failed | 202.35 seconds | `focused.log` |
| Corrected watcher/attachment/refusal and added clear cases | 102 passed | 80.83 seconds | `corrections.log` |
| Complete unit/integration regression | 2,885 passed; exit 0 | 1,543.58 seconds (25 minutes 43 seconds) | `offline.log`, `offline.xml` |

The final single invocation passed **1,063 unit and 1,822 integration cases**, including
all 318 G03 cases and the earlier G02 additions. The JUnit artifact independently records
2,885 tests with zero failures, errors or skips. No xfails/xpasses were reported. This is
the current complete offline baseline after the final shared-fixture corrections, not a
sum of focused runs. No further rerun was needed after this passing result.

The initial relation failures used the wrong expected code for a native 403: the contract is
`access_denied`, distinct from the application permission policy's `permission_denied`.
The expectation was corrected without changing runtime error mapping.

The 62 subsequent failures exposed mistakes in the newly authored mock/fixtures: watcher
POST parsing omitted the `watcher` wrapper, DELETE parsing retained `.json`, and a control
attachment with ID 10 still had attachment 9's download URL. The control URL was corrected;
the runtime URL/identity guard was preserved. The single offline attachment diagnostic in
`attachment-diagnostic.log` used DEBUG to identify that guard and is not G04 acceptance.

The corrected run covered all watcher/attachment cases, both-boundary relation proof
refusals and eight newly added clear-versus-omitted payload cases. It passed without skips.
No runtime defect or required production change was identified in these stages.

The full offline regression runs from Git Bash:

```bash
uv run --frozen pytest tests/unit tests/integration -q \
  --junitxml=.local/testing/g03-2026-10-14/offline.xml
```

Scoped Ruff lint and formatting checks passed for all nine new/changed Python files;
the shared-fixture whitespace check passed. The full run reported 19 warnings: one existing
`PydanticDeprecatedSince211` warning and 18 `PytestWarning` records because the existing
membership-budget cases use `record_property` with the default JUnit `xunit2` family.
The latter were triggered by this run's XML reporting option; they are a report-format
compatibility limitation, not failed scenarios. The artifact is retained as emitted, and
pytest configuration was not changed to suppress warnings. No runtime mypy, architecture,
coverage-percentage or native acceptance result is claimed by these scoped checks.

G03 is complete for WRT-01..07 within this offline scope. F03's shared production oracle is
removed and the selected older-writer depth in F04 is addressed. Broader native acceptance
and unselected argument/role/plugin matrices remain separate.

## Remaining scope

These are offline assertions using in-process REST/MCP, personal-key authentication and
mocked native responses. No E2E, Inspector/browser, real Redmine request, stack preparation,
native mutation or cleanup, plugin installation or global-setting change occurred.

The clear/omission and copy tests prove client payload/query and receipt handling; they do
not establish real native copy inheritance or every optional-field permission. Likewise,
attachment deletion proves the selected visible container observation, not stored-byte
removal; relation assertions do not verify native rescheduling or journal side effects.
Those native matrices remain G05/G07 and the original owner tasks' scope. Existing GET retry
and all-writer 5xx cases are reused rather than duplicating every transport failure across
every new argument combination. G04 and the remaining packages are separate assignments.
