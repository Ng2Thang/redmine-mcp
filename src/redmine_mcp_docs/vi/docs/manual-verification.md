# Xác minh thủ công :id=manual-verification

> Bản tiếng Việt được biên tập từ [tài liệu tiếng Anh gốc](#/docs/manual-verification.md). Bản gốc là nguồn chuẩn cho hợp đồng và hồ sơ đầy đủ. Tên API, lệnh, ngày, waiver và giới hạn nghiệm thu được giữ nguyên; việc dịch không thực hiện kiểm thử.

## Phạm vi và cho phép thực hiện :id=scope-and-authorization

Tài liệu mô tả quy trình, không tự cho phép thực hiện. Chỉ chạy test, startup, Inspector hoặc
live call trong giai đoạn xác minh được giao rõ ràng. Rà soát tài liệu đọc source/prose/example/link,
không chạy ví dụ. Reader smoke không cho phép mutation, tạo fixture hoặc đổi quyền.

[Ledger ngày 2026-10-07](testing/evidence/current-catalog-acceptance.md) thay trạng thái pending cũ
cho danh mục 17 đọc/15 ghi của ngày đó:1.086 offline / 21 live trên Redmine 7.0.2 thuộc sở hữu pass; gồm version/membership,
allowed_all, Inspector discovery và ba read, **không Inspector mutation PREP-020**.
H1..H6 vẫn giữ giới hạn lịch sử. Kiểm tra lại là công việc mới, không bằng chứng đã thực hiện.
Preparation/time-entry mới có acceptance/waiver/gap trong [lộ trình](plans/index.md#current-status-2026-10-09).

## Activity project (đã miễn kiểm thử) :id=project-time-entry-activities-testing-waived

TOOL-040 `list_project_time_entry_activities`, GET/api/v1/projects/{project_id}/time-entry-activities:
người dùng miễn test **2026-10-08**, runtime chưa verify. TOOL-040-001..005 chỉ chạy khi được giao riêng:

- Offline: strict project/activity ID/name, exact include mapping, upstream error, reader annotation;
  cập nhật argument map/fake project reader. Present empty khác omitted expansion; chỉ omitted
  có `/items not_returned`. Chặn null/nonarray/duplicate/malformed/name/project identity sai.
- Owned có marker Redmine 7.0.2: so populated/empty native activity, permitted/no-view, inactive/override/forbidden,
  ghi actual runtime version. Inspector cùng project kiểm ID/name/visibility/capability conditional
  view_time_entries; catalog không xác định caller default hoặc cấp log_time.
- Synthetic setup nếu được cho phép thì chỉ track/restore fixture task-owned. Không dùng Redmine 6.0.5 dùng chung
  localhost:3000 thay Redmine 7.0.2 được ghim. Reader này không ghi time/quản trị activity.

## Tạo time entry (còn chờ kiểm thử) :id=own-time-entry-creation-testing-pending

TOOL-041 `create_time_entry`, POST/api/v1/issues/{issue_id}/time-entries; coding chỉ static check.
TOOL-041-001..009 cần assignment riêng:

- Request/service/gateway: numeric/date/null/user-project-custom-batch field, strict ID/comment,
  exact POST/resolved project query, caller attribution/native default.
- Pinned/personal auth, disabled writer/account/operation/CSV/allowed_all, log_time theo issue project,
  conditional/unknown/native denial, caller log-own nhưng không view time entry.
- Independent GET accepted/mismatch/unavailable, native minute/two-decimal rounding, bad/empty201,
  5xx/dispatched timeout/pre-dispatch failure; chỉ mộtPOST, giữ uncertainty kể cả GET match.
- Catalog/schema/discovery/annotations/capability và reader/writer compatibility; mở rộng synthetic
  mock riêng writer, không thay test cũ trước assignment đó.
- Redmine 7.0.2 thuộc sở hữu: hai log 8 giờ task-owned ngày rõ ràng, so native ID/caller/date/activity; role/project default,
  thiếu default/activity sai/comment bắt buộc/daily partial success/closed/future/permission.
- Owned response-loss/500 injection, đối chiếu ambiguous commit, chỉ cleanup exact task-created IDs
  theo mechanism được phép. Xóa entry không undo webhook. Inspector creation là live write cần explicit
  authorization; không reset Redmine 6.0.5 dùng chung hoặc coi đó là target acceptance.

## Nghiệm thu cập nhật time entry :id=time-entry-update-acceptance

TOOL-042 PUT/api/v1/issues/{issue_id}/time-entries/{time_entry_id}; người dùng giao testing
**2026-10-08**. [Bằng chứng](testing/evidence/tool-042-testing.md):61 unit / 99 integration riêng,
10 native/Inspector trên môi trường thuộc sở hữu, exact cleanup và scoped checks. Full offline 1.755 pass cộng một old
catalog-argument failure sửa bằng targeted rerun pass; bảy case muộn pass riêng.
**Không có clean final full-suite rerun được công bố.** Regression mới giữ:

- Partial update strict, supplied null/empty/unknown, clear comments/date/hour/activity, exact
  issue/entry/project/user preflight; malformed/wrong target không gửi PUT; omitted không payload.
- Credited user khác author; own/all/no-edit/log-only, pinned/personal/gates/discovery/capability/CSV/
  allowed_all; role evidence conditional/unknown, native final.
- Native 204/rounding/match/mismatch/unavailable/GET failure/5xx/timeout, một PUT, giữ acceptance/uncertainty;
  mở rộng fixture không giảm reader/creation coverage.
- Redmine 7.0.2 thuộc sở hữu exact disposable ID, native field/identity/omitted/control/role-policy/concurrency/fault,
  Inspector write được giao riêng, state và cleanup ghi rõ. Không dùng #919–#924 hoặc đổi shared server
  chỉ để test. Acceptance scoped current native policies; không production/exhaustive plugin/policy/race.

## Nghiệm thu xóa time entry :id=time-entry-deletion-acceptance

TOOL-043 DELETE/api/v1/issues/{issue_id}/time-entries/{time_entry_id}, testing giao riêng
**2026-10-08**. [Bằng chứng](testing/evidence/tool-043-testing.md):32 unit / 82 integration riêng,
**1889 clean full offline pass**,12 native/Inspector trên môi trường thuộc sở hữu, scoped check/cleanup.
Regression mới giữ TOOL-043-001..009:

- Positive IDs, exact entry/issue/project/credited user preflight; missing/project-only/malformed
  không gửi DELETE. Một native DELETE không body/query/retry.
- Own credited user khác author, all/no-edit/no-view/pinned/personal/gate/CSV/allowed_all,
  conditional capability và destructive/non-idempotent hint; giữ reader/update/create fixture coverage.
- Native 204/timeout/5xx/unexpected 2xx/validation/pre-dispatch; GET not_found/still_present/unavailable
  không đổi outcome; preflight 404 lần lặp không mutation thứ hai.
- Owned có marker Redmine 7.0.2, isolated writer/Inspector, chỉ disposable ID đã ghi. Chứng minh native absence,
  spent totals/control entries, own/all/denied/fault/visibility/race, receipt từng call. Caller 404 không
  đủ. Đối chiếu uncertain, cleanup exact, ghi limits. Không #919–#924/shared/global policy changes
  chỉ để test. Plugin/policy/infrastructure rộng hơn chưa nằm trong scoped acceptance.

## Retry GET Redmine có giới hạn :id=bounded-redmine-get-retries

PREP-027 có [103 focused offline, 2 owned live reader, startup/Inspector + 3 read](testing/evidence/prep-027-testing.md)
và full regressions/targeted correction theo record. Regression mới không fault-test shared/real server:

- Exception/status eligible rồi success/exhaustion, giữ REST/MCP mapping/parameters/count attempts.
- Retry-After seconds/date/malformed/repeated/cap/jitter/disabled, controlled clock/sleep;
  đóng response và release capacity trước wait.
- Partial stream/cancel/per-GET và parent deadline/request-byte budget/cooperative batch sau accepted
  mutation; invalid JSON/model/metadata/permissions/HTTP 500/saturation chỉ một attempt.
- Giữ caller key/sanitized log, một internal REST dispatch/mutation. Read-back GET lỗi không replay
  tool/batch/session/mutation, vẫn receipt gốc.

## Ranh giới tương thích MCP :id=mcp-compatibility-boundary

PREP-026 SDK-026-001..006 được giao **2026-10-07**, [record hiện tại](testing/evidence/prep-022-026-testing.md).
Vendor private access chỉ ở mcp/compatibility.py. Inject package metadata/hook request-handler-cache-
context-transport-lifecycle sai, startup phải fail an toàn trước ready; dùng pinned pair thật, không
cài alternate version. Fixture patch compatibility module, server/transport valid shape.
Kiểm union/null schema/two-callers/immutable cache/discovery/cross-caller session rejection,
DELETE JSON/budget/error/one-mutation receipts. Manager fail-before-ready/cancel trước coroutine,
sau entry/repeated entry/shutdown error; ready chỉ sau run yields, không hang, task settles,
hai HTTP client đóng đúng thứ tự. Native/Inspector Redmine 7.0.2 thuộc sở hữu và cleanup riêng; coding waiver/handoff
cũ là lịch sử, không thay testing record mới.

## Trường upstream khai báo :id=declared-upstream-fields

PREP-025 FIELD-025-001..006 có [bằng chứng](testing/evidence/prep-022-026-testing.md).
Parametrize root/nested/list/parent/custom-field/receipt ID với bool/string/float/zero/negative;
strict flag/nonnegative counts/sizes/0..100 progress/positive project status/signed-null delay.
Safe error không raw Pydantic input. Fixture journal/watcher/attachment cần native required fields,
không chỉ identity; giữ date/hour/default/omitted-null/empty/parent dictionary/unknown policy.
Malformed preflight zero mutation; accepted write malformed GET một mutation, receipt giữ,
verification unavailable. Copy/update issue malformed progress/flag/nested refs không gửi POST/PUT.
Live parity chỉ Redmine 7.0.2 thuộc sở hữu ordinary restricted writer, state và owned cleanup.

## Admission request body :id=request-body-admission

PREP-024 BODY-024-001..006 có [bằng chứng](testing/evidence/prep-022-026-testing.md).
Raw ASGI exact cap/cap+1/missing-chunked-understated Content-Length/duplicate identical-conflicting/
negative-malformed-mismatch/non-identity encoding; safe 400/413/415, request ID, zero parser/auth/native
dispatch khi reject. Huge length/empty chunk/accepted replay/disconnect/cancel. Upload N-1/N/N+1,
default/custom cap, base64/gates không đổi; MCP POST/GET-SSE/session DELETE/internal REST mapping
không double dispatch hoặc cắt accepted response. SDK cap phải như outer middleware.
Owned upload fixture cleanup: gắn upload vào disposable issue rồi xóa issue vì native không xóa
unattached upload bằng attachment DELETE; không reset shared data. Interrupted artifact cleanup
được record riêng.

## Giờ ước lượng và time log tổng quát :id=issue-estimates-and-general-spent-time-logs

TOOL-034/035 được giao testing **2026-10-06**, dedicated offline/Redmine 7.0.2 thuộc sở hữu/Inspector pass theo task.
Trong assignment kiểm tra lại được cho phép:

```bash
uv run --frozen --no-sync pytest tests/unit/test_time_entry_search.py tests/integration/test_issue_estimates.py tests/integration/test_time_entries_overview.py -q
uv run --frozen --no-sync python scripts/prepare-e2e.py
uv run --frozen --no-sync pytest tests/e2e/test_reporting_acceptance.py --run-e2e -q
uv run --frozen --no-sync python scripts/verify-reporting-inspector.py
```

Preparation chỉ owned fixture; live test xóa issue/log riêng; Inspector tạo reader tạm rồi dừng.
Header/evidence riêng ở ignored .local/testing-e2e, không reset shared.
So same-key native estimate numeric/null/missing; tám estimate 12 giờ chỉ tổng 96 khi full scope đúng.
List time entries cross-project/inclusive spent date/project/user(me/ID)/issue, so IDs/refs/hour/date/count.
Exact project/subproject không phụ thuộc native default, project-only nullable issue, own/all role,
inaccessible/module disabled. Complete vẫn caller-visible. Dedup và decimal sum; narrowing/malformed/
budget không được biến partial thành complete.

## Nghiệm thu ba giai đoạn hiện tại :id=current-three-phase-acceptance

Người dùng cho phép implementation/execution testing **2026-10-05**. PREP-016/017/018 và
[coverage matrix](plans/testing-coverage.md) ghi selected acceptance; hạn chế assignment cũ là lịch sử.
Dùng [testing roadmap](testing-roadmap.md) cho Redmine 7.0.2 riêng/E2E/Inspector/private key.
Không nâng/reset synthetic shared chỉ để kiểm tra.

## Giới hạn đọc và link attachment :id=bounded-reads-and-attachment-links-separately-authorized

PREP-015 có selected budget/proxy/link evidence pass; ledger/matrix giữ exact scope. Cần assignment
riêng, dùng fake million-record total offline, không tạo triệu issue live.

- Broad preview có requires_narrowing; continuation scope_required trước page acquisition;
  narrow/deep/nonaligned offset, same-filter probe và bounded capability inventory.
- Safe budget errors và release permit khi concurrency/cancel/transport/close. Thử hơn configured
  limit (ít nhất 51 nếu default 50), active responses không vượt cap; thử limit nhỏ hơn.
- Time-entry aggregation guidance phải stop scope/budget, label partial/unavailable; issue breakdown
  lớn không giả định date filter không hỗ trợ. Sync conversion hết aggregate deadline trước header
  =>REST 504 read_operation_timeout, MCP giữ safe code.
- HTTP_PROXY/HTTPS_PROXY/ALL_PROXY/NO_PROXY, wildcard bypass, shared semaphore direct/proxy,
  cancel/close release. Fake credentials, không ghi proxy key thật.
- Download tool absent/cached error/retired REST 403 không fetch metadata/content. Browser link cần auth;
  không base64 content, kiểm public subpath/off-origin metadata riêng.

Coding handoff cũ về download/paging đã có testing record mới; giữ lịch sử thay vì mô tả deferral cũ
là current. Multi-user writer cần distinct private ordinary keys: excluded writer user vẫn read/connect,
khác user/key/rotated key dùng session GET/DELETE phải 404 trước dispatch; caller gốc vẫn giữ session.
PREP-014 giữ fixture matrix. Personal discovery hai user có membership khác, read schema/hint ổn định,
hidden/cached tool recheck target; đổi chỉ owned role không ảnh hưởng user khác. Public/non-member/
incomplete data là candidate, không definitive denial. Smoke không production/restore/recovery acceptance.

## Tạo Target version :id=target-version-creation-separate-authorization-required

TOOL-032 có PREP-020 selected offline/native Redmine 7.0.2/duplicate/permission/Inspector schema-read pass.
Đây là regression tương lai, không authorization mới. Redmine 7.0.2 thuộc sở hữu/restricted writer/task-owned version,
giữ Redmine 6.0.5 dùng chung và credential kín:

1. Gate chỉ operation được giao, ordinary manage_versions; schema/discovery/capability/hints.
2. Create name duy nhất, description/date, so native ID/project/exact fields/open/no-sharing.
3. Repeat name metadata khác: existing ID/data + version_already_exists; count/metadata không đổi.
4. Denied project/caller/operation/reader zero write. Manage_versions không view_issues vẫn create,
   GET verify unavailable; unreadable duplicate giữ validation error.
5. Offline timeout/malformed/shared-ambiguous duplicate/GET fail, một mutation và correct uncertainty.
6. Cleanup chỉ owned ID đã ghi, không xóa version preexisting trả về do duplicate.

## Quản lý membership :id=project-membership-management-live-authorization-required

TOOL-033 offline/lifespan/DELETE body và PREP-020 TOOL-033-011 native Redmine 7.0.2 đã pass về
managed/protected/inherited/assignee effects/cleanup; Inspector **chỉ schema/list, không mutation**.
Regression cần authorization live mới, Redmine 6.0.5 dùng chung không target evidence:

1. Authorized offline regression theo task; protected/inherited fake không thay native evidence.
2. Ordinary manager một project, denied project khác, group/direct/inherited/protected/parent-child,
   ghi baseline membership và category/project default assignee.
3. Reader list-only; Inspector 1/2 project/pagination/group/inherited/public view_members/budget;
   repeated role ID từ nhiều group/parent gộp, direct+inherited flag true; name conflict/malformed lỗi.
   Một project scope_required không chặn page hợp lệ của project khác.
4. Writer gates/operation/user/pinned-personal/capability/discovery, kể cả admin phải pass gate.
5. ID/array/extra/duplicate/linkage/group/inherited delete sai: một lỗi preflight =>zero mutations;
   incomplete inventory/malformed upstream fail safely.
6. Owned add exact payload/một attempt/state; duplicate/concurrent duplicate explicit existing không update.
   Update giữ inherited/protected, accepted mismatch và native 200/204 empty.
7. Delete eligible user, absence qua inventory bounded complete;404/access loss unavailable;
   descendant/default assignee effects riêng.
8. Mid-batch 403/422 khác shared auth/outage/budget/uncertain/cancel/GET failure; giữ accepted peers,
   stop later đúng quy tắc, no retry/rollback, fresh permission sau role revoked.
   Admission giữ đến hết deadline rồi release: no queued mutation, release permit, earlier receipts,
   later not_executed; direct/proxy và reader compatibility.
9. Reconcile pair/ID sau uncertain/interrupted, chỉ restore owned membership/role/assignment;
   record output/native/cleanup/limits. Suite count cũ không verify change mới.

## Chuẩn bị và startup :id=preparation-and-startup

Synthetic existing hoặc chủ động tạo bằng bash scripts/dev-up.sh (có tạo config/container/sample).
External chỉ read với restricted key, không seed/reset/restore. Startup phải hoàn tất rồi kiểm liveness:

```bash
curl --fail --silent --show-error http://localhost:8000/health
```

Mong đợi `{"status":"ok"}`; không contact Redmine, vẫn cần successful tool read cho connectivity/key.

## MCP Inspector :id=mcp-inspector

```bash
npx @modelcontextprotocol/inspector@2.8.0
```

Mở URL có session token, Streamable HTTP `http://localhost:8000/mcp`, private header
`X-Redmine-API-Key: <your personal Redmine API key>`. Token Inspector khác Redmine key; không chụp/log.

1. Connect/list: có get_current_user/list_issue_time_entries và readers hiện tại.
2. list_projects `{"limit":25,"offset":0}` =>visible objects/count/pagination.
3. list_issues `{"status_id":"*","limit":25,"offset":0}`, lấy ID thật.
4. get_issue issue_id thật =>matching detail và visible journal/attachment metadata.
5. list limit 1, offset 0/1 trên dữ liệu ổn định >=2 open issue =>ID khác, pagination đúng; defaultopen.
6. Filter project/closed/assigned_to_id:"me" nếu phù hợp thay đổi; me là requesting user.
7. Owned issue time entries: compare credited user/hour/date/count exact issue native; thu đủ permitted
   page trước total, ghi role visibility. Empty page không chứng minh all-user access.

Seed đầy đủ demo-mcp-reader status* expected 128; optional history expected 391 trước manual change.
Key user khác theo native visibility/count tùy role; so [dữ liệu](test-data.md)/private manifest.
Một matching count không chứng minh mọi permission boundary.

## Xác thực và validation :id=authentication-and-validation

get_current_user{} ordinary key: so ID/login/name/email/membership/role native; key user khác phải
identity khác. Inherited true/false, no membership=>[]; email thiếu=>null+/mail not_returned.
Empty membership không chứng minh zero project access; no API key/additional account metadata.
Identity mismatch/malformed membership kiểm offline, không sửa live response để giả lập.
Không header request sau expected 401 và detail missing/invalid key:

```bash
curl --silent --show-error --include http://localhost:8000/api/v1/projects
```

Inspector key thiếu/sai phải reject protected access; restore valid key kín. Swagger Authorize với key,
GET/issues limit 0=>422. Known absent/inaccessible ID không lộ content, native 403/404 tùy quyền;
không đoán sensitive ID real instance. Xem [tool reference](tool-reference.md#errors).

## Check chất lượng và ghi kết quả :id=quality-checks-and-recording-results

Chỉ chạy trong assignment cho phép:

```bash
bash scripts/check.sh
uv run --frozen pre-commit validate-config
```

Record revision/working tree, environment synthetic/external không privatehost/secret, versions,
startup/health, từng discovery/call, auth/validation/pagination, quality checks: pass/fail/not run+lý do;
known limits/deferred. Chỉ redacted summaries, không issue body/credential. Không reset/backup/restore
chỉ để validate docs. Smoke không thay automated scenarios hoặc outstanding recovery acceptance.

## Phụ lục ví dụ nguyên văn

Các đoạn mã/lệnh sau giữ nguyên từ bản gốc để tra cứu cú pháp. Không thực thi tự động; chỉ chạy bước kiểm thử hoặc mutation khi assignment cho phép.

```bash
uv run --frozen --no-sync pytest tests/unit/test_time_entry_search.py tests/integration/test_issue_estimates.py tests/integration/test_time_entries_overview.py -q
uv run --frozen --no-sync python scripts/prepare-e2e.py
uv run --frozen --no-sync pytest tests/e2e/test_reporting_acceptance.py --run-e2e -q
uv run --frozen --no-sync python scripts/verify-reporting-inspector.py
```

```bash
curl --fail --silent --show-error http://localhost:8000/health
```

```bash
npx @modelcontextprotocol/inspector@2.8.0
```

```text
X-Redmine-API-Key: <your personal Redmine API key>
```

```bash
curl --silent --show-error --include http://localhost:8000/api/v1/projects
```

```bash
bash scripts/check.sh
uv run --frozen pre-commit validate-config
```

```text
Revision / working-tree changes:
Environment: synthetic / external (no secrets or private host details)
Python and tool versions:
Startup and health: pass / fail / not run, with reason
Tool discovery and each tool call: pass / fail / not run, with reason
Authentication, validation, and pagination: pass / fail / not run, with reason
Quality checks: pass / fail / not run, with reason
Known limitations and deferred checks:
```
