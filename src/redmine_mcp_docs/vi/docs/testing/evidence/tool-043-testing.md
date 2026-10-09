# Bằng chứng kiểm thử xóa TOOL-043 :id=tool-043-deletion-testing-evidence

> Bản tiếng Việt được biên tập từ [tài liệu tiếng Anh gốc](#/docs/testing/evidence/tool-043-testing.md). Bản gốc là nguồn chuẩn cho hợp đồng và hồ sơ đầy đủ. Tên API, lệnh, ngày, waiver và giới hạn nghiệm thu được giữ nguyên; việc dịch không thực hiện kiểm thử.

**Ngày 2026-10-08**, testing được giao rõ ràng sau implementation/review. Task còn uncommitted; staged runtime edit có trước được giữ nguyên. Dùng Git Bash với locked dependency đã có, không ghi credential vào evidence.

## Coverage triển khai :id=implemented-coverage

**32 unit** kiểm identity/service/permission/receipt, uncertain/204 và real response-close error sau 204. **82 integration riêng** kiểm exact target, own/all admission, một DELETE không body, duplicate/reject, GET observation và REST/MCP. Shared fixture giữ stateful DELETE cùng bốn writer-matrix case và coverage reader/update/create.

Owned native fixture gồm disposable project/user/role/activity/entry để đối chiếu presence, control/totals, permission, independent call, fault/race và Inspector riêng.

## Runtime defect và review regression :id=runtime-defect-and-review-regression

Initial focused **305 pass/4 fail, 318,38 s** phát hiện MCP delete nhận argument chưa khai báo `entries`/`confirm`/`hours`. Registration bổ sung `additionalProperties=false` riêng cho tool theo membership pattern.

Follow-up focused **6 pass/76 deselected, 6,88 s** kiểm ambiguity caller GET 404 khi outcome uncertain và entry còn stored, cùng budget exhaustion vẫn giữ accepted receipt. Real HTTPX cleanup failure sau 204 và synthetic uncertain 204 chứng minh acceptance độc lập GET: native 204 là accepted/true; 500 hoặc unknown là uncertain/null. Không retry.

## Execution :id=execution-record

Final full offline **1.889 pass/1.035,05 s**, gồm final 32 unit/82 integration/schema fix và hai case mới; warning Pydantic có trước không bị suppress. Owned native **11 pass/272,36 s**, rồi no-issue-view bổ sung **1 pass/11 deselected, 20,82 s**. Cả 12 có passing evidence, **không có một final run cả 12**.

Inspector 2.8.0 dùng writer tạm, discovery/list/call, finally dừng và xóa private config. Scoped Ruff/format 21 runtime-test file, mypy 129 source và staged/unstaged diff pass; không claim whole-repository Ruff, debt không liên quan giữ nguyên.

## Ownership và giới hạn native :id=native-ownership-and-evidence-limits

Preflight kiểm official 7.0.2 pin, PREP-018 marker, Compose/owned volume, private baseline và native metadata. Prefix riêng, ordinary role own/all/no-edit/no-time-view/no-issue-view, project activity và ledger ownership được kiểm trước thực thi. Rails admin inspection chỉ thuộc fixture helper; **MCP không truy cập database**.

Native stored absence/control/totals chứng minh deletion; duplicate preflight 404 không gửi DELETE. Call thứ hai bị từ chối không rollback call đầu accepted. Inject 500/uncertain 204/GET 403–404 sau real deletion là application-level fault, không TCP loss. Di chuyển owned entry giữa preflight/DELETE cho thấy không lock hoặc If-Match.

Không force visibility policy native 404; observation 404 offline không chứng minh physical absence. Không kiểm mọi plugin/destruction/global policy/infrastructure. Không đổi shared user/role/settings/global activity/6.0.5 hoặc #919–#924. Settings được quan sát cho phép future/closed time, daily max 999 và required fields rỗng.

Cleanup exact ID xác nhận zero project/entry/user/role/activity, xóa ledger/Inspector config và dừng server tạm. Private cleanup JSON/log ignored.

## Traceability và nghiệm thu :id=traceability-and-acceptance

TOOL-043-001/002: strict ID/preflight/no-body/zero mutation; 003/006: credited user/permission/gate/schema/discovery/capability; 004/005: receipt độc lập presence/error và một attempt; 007/008: owned absence/control/total/role/Inspector; 009: committed fault/move race/404 ambiguity. Trạng thái complete trong offline/owned native scope; không vượt quá policy/plugin/infrastructure đã ghi.
