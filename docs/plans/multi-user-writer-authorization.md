# Multi-user writer authorization roadmap

Planning date: 2026-10-05. Target: the repository-pinned Redmine 7.0.2 release.
This document plans a change; it does not describe deployed behavior or authorize testing.
Task status is tracked in the [dashboard](index.md). Existing task IDs and acceptance evidence
remain intact. No new public MCP operation is proposed.

## Requested outcomes and ownership

| Client outcome | Current coverage | Owner | Delivery |
|---|---|---|---|
| Understand which permissions can be derived from a personal key and how sessions preserve identity | Identity exists; effective permission and session contracts are incomplete | [prep-010](tasks/prep-010-permission-session-contract.md) | Evidence and contract prerequisite |
| Multiple users access the writer using their own keys | Writer accepts one configured digest | [prep-011](tasks/prep-011-multi-user-writer-auth.md) | Phase 1 |
| Calls respect project, resource, and operation permissions | Deployment operation gate plus upstream checks; no caller permission model | [prep-012](tasks/prep-012-project-resource-authorization.md) | Phase 2 |
| Discover tools relevant to the authenticated caller | One catalog generated at startup | [prep-013](tasks/prep-013-caller-tool-discovery.md) | Phase 2 |
| Trust isolation, permission changes, and resulting write state | Earlier writer acceptance remains pending | [prep-014](tasks/prep-014-multi-user-writer-acceptance.md) | Separately authorized acceptance |

Order: prep-010 -> prep-011 -> prep-012 -> prep-013 -> prep-014.
Planning and contract review can proceed without running tests or changing Redmine state.
Implementation and verification are separate assignments. Phase 1 can deliver a common writer
catalog with per-user keys; it must not claim caller-specific discovery is already implemented.

## Design decisions

1. Keep the separate opt-in writer deployment, false-default `REDMINE_WRITE_ENABLED`, and
   `REDMINE_WRITER_OPERATIONS` as the deployment ceiling. Reader deployments expose no writes.
2. Introduce `REDMINE_WRITER_AUTH_MODE=pinned_key|personal_key`, defaulting to `pinned_key`.
   Existing deployments retain their current single-key behavior. In explicit `personal_key`
   mode, callers authenticate with their own `X-Redmine-API-Key` and all upstream calls use it.
   No administrator/service key or impersonation header substitutes for the caller.
3. In `personal_key` mode, `REDMINE_WRITER_USER_IDS` is an optional write admission restriction.
   Empty means any authenticated Redmine user may attempt enabled writes subject to Redmine
   permissions. A nonempty list limits writes, while other valid users can still read/connect.
   `REDMINE_WRITER_KEY_SHA256` must be empty in this mode; reject contradictory configuration.
4. Resolve roles by project and role ID, including inherited membership roles; do not map role
   names such as Developer or Manager to hardcoded tool bundles. Permissions across projects
   must never be merged for authorization of one target project.
5. Model capability evidence as `denied`, `conditional`, or `unknown`. A known necessary
   permission that is absent can deny a call. A permission that is present is conditional on
   resource visibility, tracker, ownership, workflow, fields, modules, and project state.
   Unknown coverage is not evidence of denial or approval; Redmine remains authoritative.
6. Resolve resource context through existing services/ports/gateways with the caller key.
   Keep HTTP adapters in `integrations/redmine/`, and keep services independent of FastAPI/HTTPX.
   Router dependencies enforce deployment gates; typed resource checks run after validated
   inputs and relevant target reads. Never infer context by manually reparsing raw request bodies.
7. Caller discovery filters a fresh copy of the deployment catalog. It omits known denied
   writes; conditional and unknown tools remain candidates whose calls may fail authorization.
   Existing read tools stay discoverable for valid callers because memberships do not describe
   all visible public resources. Tool names, arguments, result schemas, and annotations stay stable.
8. Initially use request-local identity/role deduplication only, with no cross-request positive
   authentication or permission cache. This avoids choosing a revocation TTL before measurement.
   Every request authenticates again. Later caching is a separate measured enhancement.
9. Bind stateful MCP sessions to caller user ID and a private credential fingerprint. A different
   caller/key cannot reuse a session; the SDK returns 404 as for an unknown session. Key rotation
   requires a new session. Authentication and
   permission refresh still apply on subsequent requests. Never log the fingerprint or key.
10. Preserve accepted/uncertain write receipts, no automatic retries, and independent read-back.
    Permission prechecks are not transactional with a write; upstream handles changes between them.

## Baseline evidence and limitations

| Evidence | Checked | Finding and limitation |
|---|---|---|
| `src/redmine_mcp/api/security.py` and `config.py` | 2026-10-05 | Writer compares one digest before identity lookup, then checks configured user IDs; applies at common authentication boundary |
| `auth/models.py`, `auth/policy.py`, `integrations/redmine/identity.py` | 2026-10-05 | Principal contains only user ID; named application permissions are shared, not role-derived |
| `mcp/registration.py`, `mcp/catalog.py` | 2026-10-05 | Startup catalog is shared; Streamable HTTP is stateful |
| Installed FastAPI-MCP 0.4.0 `server.py:146-184` | 2026-10-05 | `list_tools` returns shared `self.tools`; invocation extracts the request and forwards allowed headers; dynamic list/session binding needs an adapter contract |
| `uv.lock` | 2026-10-05 | FastAPI-MCP 0.4.0 and MCP SDK 1.30.0; avoid unrelated dependency upgrades |
| [Users API](https://www.redmine.org/projects/redmine/wiki/Rest_Users) | 2026-10-05 | Current-user endpoint and membership roles documented; wiki is not exact target-runtime acceptance |
| [Roles API](https://www.redmine.org/projects/redmine/wiki/Rest_Roles) | 2026-10-05 | Role detail contains permissions; not a complete effective-permission endpoint |
| [Official 7.0.2 archive](https://www.redmine.org/releases/redmine-7.0.2.tar.gz), local verified archive | 2026-10-05 | SHA-256 `d45e6d4c373cc3c8d33f1f4d4a2ffae1e1adb18703160707467493de7b4be591`; source read without executing Redmine |

The archive was read at `.local/upgrades/source/redmine-7.0.2.tar.gz`. It remains ignored.
Source findings:

- `app/controllers/roles_controller.rb`: index/show accept API authentication; JSON index uses
  givable roles, so do not assume it inventories built-in roles.
- `app/views/roles/show.api.rsb`: permission names and visibility settings are returned;
  tracker-specific permission restrictions are absent.
- `app/models/role.rb`: `permissions_all_trackers` and `permissions_tracker_ids` affect tracker
  checks. The API permission array cannot establish unrestricted tracker access.
- `app/views/users/show.api.rsb`: the caller's own `admin` flag is emitted; the response also
  contains the caller key, which the internal mapper must discard.
- `app/controllers/users_controller.rb`: memberships are filtered through visibility.
- `app/models/user.rb` and `project.rb`: administrator handling, public non-member roles,
  project-specific built-in group overrides, archived/closed projects, and enabled modules
  affect actual authorization. Absence from memberships does not prove no access.

No claim of a complete effective-permission API is made. The intended discovery is a candidate
list, not proof that every invocation succeeds. A requirement for an exact list including all
workflow/field/tracker restrictions would need additional authoritative Redmine support and a
separate contract; an administrator credential is not an acceptable shortcut.

## Migration and release boundaries

- Preserve pinned-key mode and previous acceptance records. Enable personal-key mode explicitly.
- Phase 1 retains common discovery and delegates resource permissions to Redmine using each key.
- Phase 2 adds evidence-based local denials and caller discovery without expanding operations.
- Update environment examples, Compose writer settings, architecture, tool reference, manual
  verification, development guidance, and changelog during the task that owns each behavior.
- The previous [release acceptance](tasks/prep-009-release-acceptance.md) evaluates its existing
  baseline. Multi-user acceptance belongs to prep-014 and cannot overwrite previous results.
- This request authorizes planning documents only. Automated tests, startup, Inspector, Docker
  mutations, seeding, resets, and synthetic writes have not been run or newly authorized.
- The historical runtime waiver is retained as history; it is not evidence for this new behavior.

## Contract blockers and next actions

The [prep-010 contract review](prep-010-contract-review.md) completed on 2026-10-05 resolves
the operation/context matrix, bounded inventory completeness, raw discovery handler, immutable
schema cache, and SDK session owner binding. prep-012/013 are now planned. The subsequent user
assignment requests implementation of all five tasks, quality checks and sequential per-prep
commits. prep-014 owns the distinct verification stage; no tests or live checks run during coding.
Runtime acceptance of existing writes and this new boundary remains pending; no production
rollout is included. The original planning-only authorization paragraph above is historical.
