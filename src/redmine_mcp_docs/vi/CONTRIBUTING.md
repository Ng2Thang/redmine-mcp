# Đóng góp

> Bản tiếng Việt được biên tập từ [tài liệu tiếng Anh gốc](#/CONTRIBUTING.md). Bản gốc là nguồn chuẩn cho hợp đồng và hồ sơ đầy đủ. Tên API, lệnh, ngày, waiver và giới hạn nghiệm thu được giữ nguyên; việc dịch không thực hiện kiểm thử.

Dùng Python 3.13, uv và Git Bash trên Windows. Runtime nằm trong `src/redmine_mcp/`, tài liệu chuẩn trong `docs/`, helper trong `scripts/`. Markdown của repository dùng tiếng Anh; bản tiếng Việt được người dùng yêu cầu nằm riêng trong `src/redmine_mcp_docs/vi/`.

## Quy tắc triển khai

- Giữ luồng **router → service → port → gateway**. Service không import FastAPI hoặc HTTPX; ngoại lệ hẹp là `from fastapi import status as http_status` để dùng hằng số HTTP status.
- MCP dùng lại REST và không truy cập PostgreSQL trực tiếp. Dùng HTTP bất đồng bộ, client được quản lý trong lifespan và context xác thực theo request.
- Dùng type hint rõ ràng, bốn dấu cách và giới hạn dòng 100 ký tự. Không đọc secret hoặc gọi mạng khi import module.
- Reader mặc định chỉ đọc. Writer cần deployment riêng, gate operation, key cá nhân và quyền Redmine gốc. Seed quản trị tách khỏi MCP.
- Giữ `operation_id` ổn định và đăng ký công cụ rõ ràng trong allowlist. Khi đổi dependency, cập nhật metadata và `uv.lock` cùng nhau.
- Không commit key, token, snapshot, trạng thái môi trường hay dữ liệu Redmine riêng tư. Cập nhật tài liệu và changelog khi hợp đồng công khai thay đổi.

## Kiểm tra và kiểm thử

Các lệnh sau là hướng dẫn; chỉ thực thi khi assignment cho phép:

```bash
bash scripts/doctor.sh
uv sync --frozen
bash scripts/check.sh
```

`check.sh` gồm lint, format, type và architecture. Pre-commit là tùy chọn, chỉ chạy ba kiểm tra và không được cài tự động. CI kiểm thử và ngưỡng coverage còn hoãn.

Ba lớp kiểm thử gồm unit, integration offline và live E2E được chọn rõ ràng. Discovery pytest mặc định chỉ chạy offline. Live E2E cần `tests/e2e --run-e2e`, môi trường tổng hợp thuộc sở hữu được ghim phiên bản và assignment cho phép. Assignment chỉ coding phải bàn giao dependency, fixture và bước kiểm thử riêng.

Kết quả 1.086 offline/21 live của PREP-020 phản ánh revision ngày 2026-10-07 và danh mục lịch sử 17 đọc/15 ghi. Danh mục hiện tại là 18/18 với bằng chứng bổ sung và khoảng trống còn lại; không suy rộng kết quả cũ cho mọi công cụ mới.

## Commit và pull request

Dùng tiêu đề commit ngắn ở dạng mệnh lệnh. PR mô tả hành vi thay đổi, issue liên quan, kiểm tra thực sự đã thực hiện, kiểm tra hoãn và tác động tương thích. Giữ patch tập trung vào phạm vi được giao.

Tham khảo [phát triển](/vi/docs/development.md), [xác minh thủ công](/vi/docs/manual-verification.md), [lộ trình kiểm thử](/vi/docs/testing-roadmap.md) và [ma trận coverage](/vi/docs/plans/testing-coverage.md).
