# prep-005-redmine-7-0-2: Pin the Redmine target

## 1. Task identity and status

| Field | Value |
|---|---|
| Task ID | prep-005-redmine-7-0-2 |
| Assigned capability | Define one Redmine 7.0.2 deployment and verify its reader contracts. |
| Status | complete - target pin accepted with runtime verification waived |
| Dependencies | [prep-004-accept-existing-baseline](prep-004-accept-existing-baseline.md) |
| Related tasks | [Master plan](../redmine-7-0-2-capabilities.md); [dashboard](../index.md) |
| Target Redmine version | 7.0.2-bookworm |
| Target decision | User confirmed Redmine 7.0.2 as the final version for prep-005 on 2026-10-02. |
| Last updated | 2026-10-02, Codex |
| Next action | Continue to tool-014 using 7.0.2 source evidence; retain the runtime evidence limitation. |

## 2. Discovery and evidence

The [official release archive](https://www.redmine.org/releases/redmine-7.0.2.tar.gz)
was checked against SHA-256
`d45e6d4c373cc3c8d33f1f4d4a2ffae1e1adb18703160707467493de7b4be591`.
The official `redmine:7.0.2-bookworm` multi-platform image index was resolved to
`sha256:5cb12288dbfb807f136adbee02d60a96acc24edad0404cbfce214a7ced39ff6a`.
The image's Ruby, Rails, database, and API behavior were inspected on 2026-10-02.
This is source and artifact evidence; no 7.0.2 runtime acceptance has been recorded.
On 2026-10-02, the user confirmed Redmine 7.0.2 as the final target version for
prep-005. This confirms the version decision, not runtime acceptance.

The [Redmine REST index](https://www.redmine.org/projects/redmine/wiki/Rest_api)
and the checked release source do not establish Documents REST for this target.
Document REST tool drafts are outside this repository's active roadmap.
Document category enumeration remains in scope through the Enumerations API.

## 3. Requirements

| Requirement | Observable behavior |
|---|---|
| REQ-001 | The synthetic deployment uses only the pinned Redmine 7.0.2 image and marked volumes. |
| REQ-002 | Existing MCP reader operations and supported Files, Attachments, and Issues REST contracts are checked against this target. |
| REQ-003 | API-key permissions, visibility, and failure outcomes are documented with dated, redacted evidence. |

## 4. Public contract and technical specification

| Area | Contract |
|---|---|
| MCP operation | None; this is a deployment prerequisite. |
| Configuration | [Synthetic Compose](../../../deploy/compose.test.yaml) pins the official image index digest. |
| Access | The reader deployment remains read-only and uses the caller's personal Redmine API key. |
| Version support | Redmine 7.0.2 only. |
| Evidence | A source check or rendered Compose file does not establish runtime acceptance. |

## 5. Implementation plan

1. Pin the synthetic image, volume labels, and snapshot version marker to 7.0.2.
2. Remove the separate version-transition deployment and its runbook.
3. Align the roadmap and task references with the single target.
4. Hand off runtime verification under the repository's testing authorization rule.

## 6. Acceptance criteria and traceability

| Criterion | Requirement | Observable result | Evidence |
|---|---|---|---|
| AC-001 | REQ-001 | Compose, volume labels, and snapshot markers identify 7.0.2 only. | Static inspection passed, 2026-10-02 |
| AC-002 | REQ-002 | Existing reader catalog and supported REST behavior pass on a marked 7.0.2 environment. | Not established; user waived live verification on 2026-10-02. |
| AC-003 | REQ-003 | Permissions and failure cases match the caller's identity. | Not established; user waived live verification on 2026-10-02. |

## 7. Test plan and execution record

Testing was planned but the user waived actual runtime verification on 2026-10-02.
The later verification stage should check the pinned image identity, application startup,
Inspector discovery and representative reader calls, same-key REST comparisons,
permission boundaries, empty and populated collections, and backup/restore behavior
on a disposable marked 7.0.2 environment. Record actual results before passing criteria.

## 8. Implementation and review record

The artifact checksum and image digest were previously inspected. Static inspection
on 2026-10-02 found one Redmine image pin, matching volume labels, and one
snapshot version marker.
The 2026-10-02
single-version revision makes the synthetic Compose deployment authoritative and removes
the separate candidate configurations. Prior live samples were collected
before this target was configured; they remain useful for reader behavior review but
do not count as 7.0.2 acceptance evidence. No runtime verification was run here.

## 9. Completion and handoff

- [x] One Redmine image version is defined in deployment configuration.
- [x] The user confirmed Redmine 7.0.2 as the final target version.
- [x] Version-transition instructions and configurations are removed.
- [ ] The marked 7.0.2 runtime passes acceptance scenarios (waived; no pass claimed).
- [x] The user accepted continuation without runtime verification on 2026-10-02.

Final status: **target pin accepted with runtime verification waived**. Source and
configuration evidence support the pinned version; live reader and permission behavior
remain unverified. The waiver permits dependent planning and coding to proceed.
