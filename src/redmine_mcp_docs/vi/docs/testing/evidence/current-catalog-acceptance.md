# Sổ nghiệm thu danh mục :id=current-catalog-acceptance-ledger

> Bản tiếng Việt được biên tập từ [tài liệu tiếng Anh gốc](#/docs/testing/evidence/current-catalog-acceptance.md). Bản gốc là nguồn chuẩn cho hợp đồng và hồ sơ đầy đủ. Tên API, lệnh, ngày, waiver và giới hạn nghiệm thu được giữ nguyên; việc dịch không thực hiện kiểm thử.

**Ngày 2026-10-07**, chủ sở hữu PREP-020. Môi trường riêng ghim Redmine 7.0.2 theo digest trong `deploy/compose.test.yaml`. Danh mục lúc đó gồm **17 đọc/15 ghi**; reader không mutation và download attachment đã retire. Revision R020 dùng Git base `533202519485ac1510e72e688fd40d6a695ac968` cộng thay đổi PREP-020 chưa commit. Hash file riêng tư không chứng minh đã có commit. Đây là evidence lịch sử, không nghiệm thu mới cho 36 operation hiện tại.

## Định nghĩa bằng chứng :id=evidence-definitions

| ID | Phạm vi được ghi nhận |
| --- | --- |
| O020 | 1.086 default offline pass, 335,59 s; gồm 49 allowed_all case và PREP-019; warning Pydantic có trước |
| A020 | 15 writer qua REST/MCP; setting, deployment ceiling, pinned/personal admission, denial và capability filter |
| L020-B | Lifecycle, native reader/writer, private/author/tracker/state, gate, inherited role/revocation, timeout và received 500 |
| L020-V | Version field/duplicate/state/count, permission và verification unavailable, SDK/capability |
| L020-M | Membership public/private, managed/protected/inherited/group, child propagation và default assignee |
| L020-H | Version/category/filter/workflow/registry/project tracker, populated date/hour log và profile |
| L020-R | Estimate parity, general log scope/date/order/own visibility, decimal total và numeric/me schema |
| I020 | Inspector 2.8.0 discovery/schema/hint, ba read version/membership/capability; **không mutation Inspector** |
| S019 | Mutation 5xx uncertainty, một dispatch, receipt/GET tách biệt, không tự tạo ID/token, batch stop |

## Sổ theo operation :id=operation-ledger

32 operation có functional acceptance trong fixture và failure matrix đã chọn. Reader bao gồm profile, project capability, project/detail/version/category/file/member, issue/detail, issue/general time log, status/tracker/priority và document category. Writer gồm upload/project file/attachment metadata-delete, version creation, ba membership batch, issue create/update/note, relation create/delete và watcher add/remove.

Mỗi operation có scenario và evidence riêng trong bảng gốc. Functional pass không đóng mọi task lịch sử, mọi policy/container hoặc release production. Tổng log vẫn chỉ phản ánh tài nguyên caller nhìn thấy; document category không cung cấp document content workflow; role API không phải toàn bộ metadata quản trị.

## Khoảng trống lịch sử :id=historical-criterion-reconciliation-and-shared-policies

| Nhóm | Giới hạn giữ lại |
| --- | --- |
| H1 — TOOL-002–012 | Chưa bao phủ mọi sharing mode, per-issue all-user visibility và filter/permission combination |
| H2 — TOOL-014–030 | Waiver 2026-10-02 giữ nguyên; chưa blanket-pass document/wiki/changeset container, cross-project scheduling, mọi field/workflow/privacy |
| H3 — TOOL-013/PREP-003 | Hai key, profile/membership/session đã chọn; locked/deleted account và mọi nullable profile variant cần follow-up; admin không thay ordinary-user evidence |
| H4 — TOOL-031/PREP-010–014 | Role merge, partial evidence, bounded filter, admission/revocation/inheritance đã chọn; không mọi container/permission/admin/partial metadata live |
| H5 — PREP-015/TOOL-034–035 | Budget/probe/aggregate/decimal/dedup có phạm vi riêng; million-record preview/saturation/malformed là fault offline, không production load hoặc global total mọi role |
| H6 — PREP-019/allowed_all | Receipt/batch/parsing/catalog có evidence; sentinel không cấp permission, không retry mutation/transaction/rollback/production activation |

Không đổi waiver thành pass. Suite count không tự đóng một tiêu chí chưa được thực hiện.

## Cleanup và ranh giới release :id=cleanup-and-release-boundary

Fixture kiểm tra owner/version/marker, tạo 4 project và 5 role dùng riêng với ordinary user sẵn có; không đổi grant/membership không thuộc fixture. Cleanup child trước parent, xác minh không còn project/role thuộc sở hữu. Revocation tạm của baseline được khôi phục trong finally. Journal history có thể còn, không rollback lịch sử. Config/log/key và native evidence nằm trong `.local/` ignored; app Inspector tạm được dừng.

## Execution cuối — 2026-10-07 :id=final-execution-2026-10-07

Offline **1.086 pass/335,59 s**, live **21 pass/115,61 s**, gồm bốn case PREP-020 riêng và baseline/reporting; teardown pass. Ruff, format 256 Python file, mypy 120 source file và scoped whitespace review pass tại thời điểm đó. Một reader test thiếu `project_ids` được sửa; không phát hiện runtime defect mới trong phần này. Không reset shared data, đổi dependency, deploy, CI hoặc publish release. PREP-009 final review, vận hành/recovery và các khoảng trống rộng hơn vẫn riêng biệt.
