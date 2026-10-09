# Lịch sử thay đổi

> Bản tiếng Việt được biên tập từ [tài liệu tiếng Anh gốc](#/CHANGELOG.md). Bản gốc là nguồn chuẩn cho hợp đồng và hồ sơ đầy đủ. Tên API, lệnh, ngày, waiver và giới hạn nghiệm thu được giữ nguyên; việc dịch không thực hiện kiểm thử.

Các thay đổi được ghi trước khi publish release. Version metadata không chứng minh đã có release. Phần dưới biên tập các mục chính của changelog chuẩn; bản tiếng Anh giữ toàn bộ lịch sử chi tiết.

## Chưa phát hành (Unreleased)

### Sửa trạng thái tài liệu — 2026-10-09

Căn chỉnh hướng dẫn với danh mục 18 đọc/18 ghi, writer key cá nhân, ngoại lệ HTTP status constants và bốn check trong `check.sh` (pre-commit vẫn ba). Sửa GET retry/discovery, thay PREP-022–026 pending bằng evidence, ghi rõ Compose không forward body-cap override, phân biệt baseline lịch sử với time-entry acceptance. Chỉ sửa Markdown; không chạy test/static/build/startup/Inspector/live/deployment. Giữ waiver, pending và Unreleased.

### Nghiệm thu và tài liệu — 2026-10-07

PREP-022–026 ghi 1.395 offline, 23 owned live Redmine 7.0.2 và Inspector 2.8.0 pass, gồm schema nullable/union, batch budget, body admission, strict field và lifecycle. CI, coverage threshold và production readiness hoãn.

PREP-020 đối soát 32 operation lúc đó với 1.086 offline/21 live, native version/membership, allowed_all và Inspector/schema/read. PREP-021 cập nhật tài liệu mà không chạy setup/verification. Task pilot deployment bị loại theo yêu cầu; các giới hạn recovery/vận hành vẫn giữ.

### Thay đổi công cụ và transport

- `delete_time_entry`: một entry gắn issue, strict linkage và own/all permission, một DELETE không body; acceptance/uncertainty tách visibility. TOOL-043: 32 unit/82 integration/1.889 full offline/12 native qua hai lượt, sửa schema `additionalProperties=false`.
- `update_time_entry`: chỉ field được cung cấp, exact linkage và credited-user permission, một PUT; TOOL-042: 61 unit/99 integration/10 native. Full run có 1.755 pass và lỗi catalog cũ; rerun sửa lỗi + 7 case muộn pass, chưa có final clean full rerun.
- `create_time_entry`: chỉ caller, issue nhìn thấy, ngày rõ ràng và giờ dương, POST một lần, verification riêng; TOOL-041 testing pending.
- `list_project_time_entry_activities`: effective native activity, validation nghiêm, missing-expansion evidence và duplicate rejection; TOOL-040 testing waived.
- `get_issue` giữ tags string array nếu upstream thực sự cung cấp. Không cài companion/plugin, thêm GET hoặc switch cấu hình. Full-tag enumeration không có. Tag assignment và task TOOL-037 bị loại theo yêu cầu; mã retire.
- `list_issues.tags_any`: ANY native, bounded input, giữ filter/count/pagination, không nhận wildcard/escape để tránh mở rộng match. TOOL-036 có offline/live/Inspector evidence trên 6.0.5; full 7.0.2, hai-tag overlap và private-role acceptance pending.
- GET retry giới hạn transport và 429/502/503/504: mặc định tối đa ba attempt, exponential backoff/jitter/Retry-After, chung deadline/request/byte budget. Mutation và internal REST dispatch vẫn một lần. PREP-027 có evidence riêng.
- Compatibility facade cô lập FastAPI-MCP 0.4.0/MCP SDK 1.30.0, kiểm tra version/hook shape, schema repair/discovery ordering và readiness/cleanup; không nâng dependency.
- Body admission trước JSON/auth, cap suy ra 10 MiB với defaults, optional `REDMINE_MAX_REQUEST_BODY_BYTES`; kiểm tra framing/encoding và sanitized errors.
- Membership batch budget riêng: 300 request, 30 MiB GET bytes, deadline 300 s; reuse proof chỉ trong preflight, refresh theo item.
- Read defaults: concurrency 50, admission 30 s, 30 attempt/deadline 90 s, 10 query page/10 MiB; environment explicit vẫn override.

### Sửa lỗi và nghiệm thu bổ sung

SDK body cap khớp ứng dụng để upload mặc định 5 MiB qua MCP. Assignment null chuyển thành native empty ID nhưng giữ expected-state null và omitted-field behavior. Strict resource/receipt ID, boolean/count/size/progress/relation delay; malformed read-back giữ receipt gốc. Schema OpenAPI nullable/union được phục hồi trước discovery/cache.

Mọi mutation JSON/binary nhận 500–599 được phân loại uncertain; cần reconciliation trước retry. PREP-019 có offline/native commit+500/Inspector evidence. `list_time_entries.user_id` giữ union số dương hoặc `"me"`; issue estimates và visibility observations được giữ. TOOL-034/035 có reporting evidence. Membership role trùng được normalize, permission nguồn kế thừa giữ lại; deadline được kiểm tra sau admission để không dispatch write đã hết hạn.

### Các capability đã bổ sung trong lịch sử

Version creation tạo open/unshared Target version, báo duplicate theo contract. Membership batch add/update/remove có whole-batch preflight, giới hạn mười item/project, user-only permission và acceptance/read-back riêng; native acceptance ban đầu pending rồi pass PREP-020.

Read budget/pagination/capability scan bị giới hạn. Attachment chỉ metadata/browser link, optional public URL mapping; `download_attachment` và REST content route đã retire. `list_my_project_capabilities` báo permission deduplicated, known/partial/unknown và conditional tool candidate; optional reason/filter không cấp quyền.

Writer personal-key hỗ trợ nhiều caller, optional write-user admission, pinned-key compatibility và credential-bound session. Discovery theo caller dùng schema superset bất biến; gọi trực tiếp/cached vẫn kiểm tra request permission. Các writer issue/note/relation/watcher/upload/project file/attachment có single dispatch và verification riêng.

Các reader bổ sung profile hiện tại, project, status/category/version/member/file, issue detail/filter/expansion, issue time entries và reporting scope. Permission/visibility luôn theo Redmine. Synthetic target được ghim 7.0.2; draft Document REST không hỗ trợ bị loại.

Các cải tiến runtime lịch sử gồm session manager readiness, typed message constants, public package exports và architecture checks, auth context theo normalized key, streamed payload cap/deadline, startup contract checks, immutable query validation, lifespan cleanup, HTTP pooling/cookie isolation, correlated sanitized error/timing, strict envelope/pagination/resource identity và `X-Redmine-API-Key` riêng cho caller. Shared runtime credential/bearer settings đã retire.
