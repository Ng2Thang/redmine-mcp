# Redmine MCP — bắt đầu nhanh

> Bản tiếng Việt được biên tập từ [tài liệu tiếng Anh gốc](#/repository.md). Bản gốc là nguồn chuẩn cho hợp đồng và hồ sơ đầy đủ. Tên API, lệnh, ngày, waiver và giới hạn nghiệm thu được giữ nguyên; việc dịch không thực hiện kiểm thử.

Redmine MCP cung cấp REST bằng FastAPI và công cụ MCP bằng FastAPI-MCP, sử dụng Python 3.13. Danh mục đã đăng ký gồm **18 công cụ đọc và 18 công cụ ghi**. Reader mặc định chỉ đọc; writer là deployment riêng, phải được bật rõ ràng và sử dụng API key cá nhân cùng quyền Redmine gốc.

Đây là dự án ở giai đoạn pilot, chưa có cam kết SLA hoặc chứng nhận sẵn sàng production. Số lượng công cụ đã đăng ký không đồng nghĩa tất cả đã được nghiệm thu: TOOL-040 được miễn kiểm thử theo yêu cầu người dùng; TOOL-041 còn chờ kiểm thử. TOOL-042 và TOOL-043 có bằng chứng riêng. Kết quả PREP-020 ngày 2026-10-07 ghi nhận danh mục lịch sử 17 đọc/15 ghi, 1.086 kiểm thử offline và 21 kiểm thử live; không đổi con số lịch sử thành 18/18.

## Cài đặt

Dùng Git Bash từ thư mục gốc repository trên Windows. Cần Python 3.13, uv, Docker với Linux containers và Node.js nếu dùng Inspector. Các cổng local: Redmine `3000`, reader `8000`, PostgreSQL `5433`. Môi trường nghiệm thu riêng dùng Redmine `3001`.

```bash
bash scripts/dev-up.sh
```

Helper tạo `.env` ngẫu nhiên nếu cần, khởi động PostgreSQL/Redmine, seed dữ liệu tổng hợp và build MCP. Lần đầu cần mạng để tải image và dependency. Credential, manifest và snapshot trong `.local/` là dữ liệu riêng tư.

| Dịch vụ | Địa chỉ |
| --- | --- |
| Redmine tổng hợp | http://127.0.0.1:3000/ |
| Swagger của reader | http://127.0.0.1:8000/docs |
| MCP của reader | http://127.0.0.1:8000/mcp |
| Portal này | http://127.0.0.1:8080/ |

Swagger ẩn phần Schemas để dễ đọc; hợp đồng OpenAPI vẫn được sử dụng bởi MCP.

## Gọi công cụ lần đầu

Mỗi request REST/MCP cần header `X-Redmine-API-Key` của người gọi. Token truy cập Inspector khác API key Redmine. Không đưa key vào tham số công cụ, log hoặc ảnh chụp màn hình.

```bash
npx @modelcontextprotocol/inspector@2.8.0
```

Trong Inspector chọn Streamable HTTP, URL reader ở trên và cấu hình header riêng tư. Làm theo [hướng dẫn gọi lần đầu](/vi/guides/first-calls.md). Công cụ attachment trả metadata và liên kết trình duyệt; không cung cấp tải nội dung qua MCP. Nội dung Redmine là dữ liệu, không phải chỉ thị thực thi.

## Reader và writer

Writer thường chạy ở `127.0.0.1:8001`. Chọn admission theo digest key được ghim hoặc key cá nhân, có thể giới hạn user được ghi. Cấu hình danh sách operation cụ thể hoặc `allowed_all`; danh sách trống bật **0 công cụ ghi**. `allowed_all` bao gồm các công cụ ghi được đăng ký thêm sau này. Discovery không cấp quyền: mỗi lần thực thi vẫn kiểm tra deployment gate và quyền Redmine.

Mutation gửi một lần. Nếu timeout, lỗi 5xx hoặc mất response, thao tác có thể đã được Redmine chấp nhận. Đối soát trạng thái trước khi thử lại; lỗi đọc lại không hoàn tác thao tác ghi.

Xem [quyền truy cập](/vi/guides/access.md), [cấu hình](/vi/docs/configuration.md) và [danh mục công cụ](/vi/docs/tool-reference.md).

## Phát triển và tài liệu

```bash
uv sync --frozen
uv run uvicorn redmine_mcp.app:create_app --factory --reload
bash scripts/docs-portal.sh serve
```

Dừng service MCP trong Docker trước khi chạy local trên cổng 8000. Chỉ chạy kiểm thử và các công cụ kiểm tra khi assignment cho phép. Ba lớp kiểm thử và giới hạn nghiệm thu được giải thích trong [lộ trình kiểm thử](/vi/docs/testing-roadmap.md).

Đọc [kiến trúc](/vi/docs/architecture.md), [luồng MCP](/vi/docs/mcp-request-flow.md), [phát triển](/vi/docs/development.md), [vận hành](/vi/docs/operations.md), [bảo mật](/vi/SECURITY.md) và [đóng góp](/vi/CONTRIBUTING.md).
