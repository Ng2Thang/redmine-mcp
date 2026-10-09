# Rà soát trạng thái tài liệu — 2026-10-09

> Bản tiếng Việt được biên tập từ [tài liệu tiếng Anh gốc](#/docs/reviews/documentation-state-audit-2026-10-09.md). Bản gốc là nguồn chuẩn cho hợp đồng và hồ sơ đầy đủ. Tên API, lệnh, ngày, waiver và giới hạn nghiệm thu được giữ nguyên; việc dịch không thực hiện kiểm thử.

## Phạm vi và giới hạn

Bản rà soát gốc ngày 2026-10-09 dùng HEAD `e6ad1e0`. Working tree đã có thay đổi ở `write.py` và `tests/e2e/test_live_acceptance.py`; các thay đổi đó được giữ nguyên. Chỉ đọc source, tài liệu và metadata Git. Không chạy test, lint, type/architecture checker, dependency install, build, startup, Inspector, live call, deployment hay recovery.

Ban đầu chỉ báo cáo; sau đó người dùng cho phép sửa Markdown. Không kiểm tra từng dòng của mọi task hoặc mọi link. Đây là hồ sơ lịch sử, không phải kiểm chứng lại revision hiện tại.

## Các phát hiện

Baseline được quan sát gồm Python 3.13, REST/MCP, 18 đọc/18 ghi, reader 8000/writer 8001, Redmine 7.0.2 được ghim digest, FastAPI-MCP 0.4.0, MCP SDK 1.30.0 và version metadata 0.1.0 với changelog Unreleased.

Một số hướng dẫn còn mô tả read-only/future writer, số lượng reader cũ, GET không retry, discovery không inventory hoặc PREP-022–026 pending. `check.sh` thực tế gồm bốn kiểm tra; pre-commit tùy chọn gồm ba. Ngoại lệ import HTTP status constants và quy tắc commit cũng cần căn chỉnh.

Base Compose không forward `REDMINE_MAX_REQUEST_BODY_BYTES`; nếu cần override phải cấu hình rõ ràng. Package metadata còn mô tả read-only và thiếu README URL. Tại thời điểm kiểm tra, license/release tag/workflow GitHub chưa được theo dõi đầy đủ; địa chỉ bảo mật riêng chưa công bố. Remote protection không được kiểm tra.

PREP-020 ghi 1.086 offline/21 live cho danh mục 17 đọc/15 ghi lịch sử; không sửa thành 36 operation. TOOL-043 có 1.889 full offline pass và 12 native case qua hai lượt, không phải kiểm thử mới của dirty tree hiện tại.

## Công việc còn mở

- TOOL-040 waived; TOOL-041 pending acceptance.
- Tag evidence trên 6.0.5 không đóng toàn bộ 7.0.2/private-role/overlap acceptance.
- PREP-028 và BUG-001 sanitization còn công việc/giới hạn; packaging isolation, recovery và operational readiness hoãn.
- PREP-009 release readiness còn blocked; metadata version không chứng minh release đã publish.

## Các sửa đổi Markdown được ghi nhận

AGENTS, development/operations, request flow, roadmap, README/contribution/manual testing và changelog được căn chỉnh theo danh mục/gate/key cá nhân hiện có. GET retry và caller-specific discovery được sửa mô tả; first-attempt discovery gồm ba GET. PREP-022–026 trỏ tới evidence functional acceptance, giữ nguyên giới hạn.

Không đổi runtime/config/tests trong phần sửa tài liệu này và không thực thi check. Waiver, acceptance pending, Unreleased status và thay đổi có trước được giữ nguyên. Metadata, Compose override, license/contact, CI, verification và publication là công việc riêng.

## Checklist trước release

Chọn phạm vi pilot hay production và artifact mục tiêu; cập nhật tài liệu; căn chỉnh metadata/version/changelog/license/contact; review hai thay đổi có trước và revision release sạch; xác nhận waiver. Sau đó chỉ khi được cho phép mới chạy static/offline/native 7.0.2/Inspector và artifact checks. Production còn cần operational/recovery/rollback và native permission acceptance. Cuối cùng cập nhật PREP-009 rồi quyết định tag/publish. Checklist không tự cấp phép hoặc chứng minh release đã xảy ra.
