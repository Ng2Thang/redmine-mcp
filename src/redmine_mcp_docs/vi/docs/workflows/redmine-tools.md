# Quy trình triển khai công cụ MCP :id=mcp-tool-implementation-workflow

> Bản tiếng Việt được biên tập từ [tài liệu tiếng Anh gốc](#/docs/workflows/redmine-tools.md). Bản gốc là nguồn chuẩn cho hợp đồng và hồ sơ đầy đủ. Tên API, lệnh, ngày, waiver và giới hạn nghiệm thu được giữ nguyên; việc dịch không thực hiện kiểm thử.

Quy trình áp dụng cho capability hướng người dùng hoặc prerequisite chung. Bắt đầu từ outcome/client và catalog hiện có, không chuyển mọi REST endpoint thành MCP tool. Redmine documentation/versioned source là evidence, không tự mở scope. Dùng [dashboard](../plans/index.md), task và [template tiếng Anh](../templates/redmine-tool-task.md). Task/canonical Markdown vẫn tiếng Anh; bản portal Việt là ngoại lệ được yêu cầu. Lệnh dùng Git Bash.

## Input và trách nhiệm :id=inputs-and-ownership

Brief xác định caller/outcome/input/output/read-write. Nếu chưa có task, đọc catalog/code/requirement và ưu tiên reuse hoặc mở rộng tool phù hợp. Một task một public behavior; prerequisite dùng task riêng. Đọc instruction, contributor guide, architecture, reference, config, template, code và Compose pin/dependency.

Giữ thay đổi working tree không liên quan và retired ID. Chỉ renumber khi được yêu cầu, đồng bộ filename/ID/dependency/link/scenario/dashboard. Ghi source URL, ngày, target version và claim chưa xác minh; đối chiếu 7.0.2. Status/blocker/next action đồng bộ giữa task và dashboard. Planned là quyết định contract đủ rõ dù dependency có thể pending; không đồng nghĩa implemented.

## Giai đoạn assignment :id=assignment-stages

| Giai đoạn | Output |
| --- | --- |
| Discovery | Catalog/code/permission/version evidence, coverage và uncertainty |
| Requirements | Outcome/scope và tiêu chí quan sát được |
| Specification | MCP/REST/upstream/error/compatibility, giải quyết quyết định quan trọng |
| Planning | Thứ tự edit, dependency và verification plan đủ để triển khai |
| Implementation | Code/registration/docs/record, behavior đã có |
| Verification | Các check/test/native scenario được phép pass hoặc blocker cụ thể |
| Handoff | Status/next action; complete khi đủ required evidence |

Plan-only/review-only dừng đúng stage. Skill `redmine-implement-task` chỉ code/docs/Ruff/mypy, không viết/chạy test/startup/Inspector/live; bàn giao testing riêng. Testing-only task hoặc full roadmap phải cho phép stage rõ ràng. Static không thay runtime acceptance.

## Agent roadmap tuần tự :id=sequential-roadmap-agent

`redmine_feature_agent` chỉ thực thi range/order được giao, một task mỗi lần, không spawn thêm. Đọc skill theo stage, kết thúc coding trước testing và đồng bộ evidence. Chỉ vượt blocked task để làm independent selected task có dependency hoàn tất; không coi prerequisite blocked là xong. Mô tả này không yêu cầu spawn agent cho việc dịch portal.

## Kiến trúc và truy cập :id=runtime-architecture-and-access

Giữ router → service → Protocol port → gateway, async/lifespan/typed validation/sanitization/key cá nhân và hẹp exception HTTP status constants. REST trước MCP, operation ID ổn định, explicit allowlist; không PostgreSQL/generic CRUD proxy/log key-token-issue body. Reader read-only, writer opt-in riêng/gate/native permission.

Writer spec định effect, least permission, policy, disposable verification, native success status/body, duplicate/retry/timeout uncertainty, partial outcome/concurrency/reconciliation/cleanup. Không tự hứa idempotency/rollback; failed GET không chứng minh write thất bại. Seed quản trị riêng.

## Xác minh :id=verification

Baseline dùng pytest/asyncio/MockTransport/ASGI lifespan/fake settings/SDK client, mặc định không Docker/mạng/key thật. Case có ý nghĩa cho success/input/page/empty-malformed/auth/permission/timeout/discovery/invocation/error/compatibility. Native chỉ trên owned marked environment khi opt-in; không seed/reset/restore chỉ để validate reader.

Khi được giao, ghi command/result thật, phân biệt mock/live, cập nhật Inspector scenario và build khi scope packaging/dependency yêu cầu. Complete cần behavior/docs/check/test/native evidence theo tiêu chí task. Code xong nhưng verification blocked phải ghi blocker/next action, không fake acceptance.

## Ví dụ bàn giao :id=example-handoffs

Planning assignment yêu cầu plan tool tìm version của project nhìn thấy và dừng sau kế hoạch. Coding assignment dùng `redmine-implement-task` cho task đã chọn, triển khai code/docs/static rồi handoff test. Các ví dụ không tự cấp quyền execution.
