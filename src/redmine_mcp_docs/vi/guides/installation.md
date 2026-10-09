# Cài đặt

Chọn môi trường Docker với dữ liệu tổng hợp do bạn quản lý để đánh giá, hoặc chạy Python
local với một Redmine bạn có quyền truy cập. Ứng dụng hướng tới Redmine 7.0.2.
Dùng Git Bash trên Windows và chạy các lệnh dưới đây từ thư mục gốc repository.

## Chuẩn bị

| Thành phần | Mục đích |
| --- | --- |
| Git Bash và Git | Lệnh repository và các script Bash |
| Python 3.13 và uv | Phát triển local, cài dependency theo lockfile |
| Docker Desktop với Linux containers | Môi trường Redmine/PostgreSQL/MCP tổng hợp |
| Node.js/npm | MCP Inspector khi bạn chọn sử dụng |

Riêng portal tài liệu chỉ cần thư viện chuẩn Python, Git để xác định file xuất và các asset
trình duyệt local. Không cần Docker, Node, API key hay Redmine đang chạy.

## Cách A: môi trường Docker tổng hợp

```bash
bash scripts/dev-up.sh
```

Script tạo thông tin đăng nhập ngẫu nhiên riêng trong `.env` nếu chưa có, khởi động dịch vụ,
seed dữ liệu mẫu và chạy MCP. Tải image và build lần đầu cần Internet.
Không copy `.env.example` vào quy trình này hoặc trộn cấu hình server thật vào môi trường tổng hợp.

| Dịch vụ | Địa chỉ mặc định |
| --- | --- |
| Redmine | `http://localhost:3000` |
| Swagger | `http://localhost:8000/docs` |
| MCP Streamable HTTP | `http://localhost:8000/mcp` |
| Liveness | `http://localhost:8000/health` |
| Cổng PostgreSQL trên host | `5433` |

Xem [vận hành](/vi/docs/operations.md) về tài khoản, dừng/khởi động lại, seed và công cụ dữ liệu.
Không chạy script seed/reset/restore dữ liệu tổng hợp trên Redmine thật.

## Cách B: Python local

Chuẩn bị công cụ và dependency đã khóa phiên bản:

```bash
bash scripts/doctor.sh
uv sync --frozen
```

Theo [cấu hình Redmine bên ngoài](/vi/docs/configuration.md#external-redmine) để đặt
`REDMINE_URL` có thể truy cập. Cấu hình được đọc khi tạo ứng dụng từ `.env` tại thư mục gốc;
biến môi trường của process được ưu tiên. Mỗi client cung cấp key trong request,
không dùng API key runtime chung.

Dừng dịch vụ MCP Docker trước khi dùng cùng cổng ở local. Sau đó chạy reader:

```bash
uv run --frozen uvicorn redmine_mcp.app:create_app --factory --host 127.0.0.1 --port 8000 --reload --no-access-log
```

Swagger vẫn ở `/docs`; portal tài liệu chạy trên listener riêng. Cài đặt không tự cho phép
kiểm thử. Chỉ chạy công cụ chất lượng hoặc test trong công việc được cho phép kiểm tra.

## Mở portal tài liệu

```bash
bash scripts/docs-portal.sh serve
```

Mở `http://127.0.0.1:8080/#/vi/`. Có thể chọn cổng khác:

```bash
bash scripts/docs-portal.sh serve 8088
```

Nhấn Ctrl+C để dừng. Script xuất tài liệu hiện tại trước khi khởi động; hãy khởi động lại
sau khi chỉnh sửa. Hiển thị, tìm kiếm, tô màu mã và sơ đồ dùng asset offline.
Điều này không làm lệnh cài dependency hay request tới Redmine hoạt động offline.

Đọc tiếp [gọi REST/MCP lần đầu](first-calls.md) hoặc [quyền reader và writer](access.md).
