# Vận hành và xử lý sự cố

> Bản tiếng Việt được biên tập từ [tài liệu tiếng Anh gốc](#/docs/operations.md). Bản gốc là nguồn chuẩn cho hợp đồng và hồ sơ đầy đủ. Tên API, lệnh, ngày, waiver và giới hạn nghiệm thu được giữ nguyên; việc dịch không thực hiện kiểm thử.

Chạy lệnh bằng Git Bash từ repository root. Cần Docker Linux containers và Python 3.13. Môi trường tổng hợp sử dụng cổng Redmine `3000`, reader `8000`, PostgreSQL `5433`; writer riêng dùng `8001`.

## Khởi động và dừng

```bash
bash scripts/dev-up.sh
```

Helper tạo `.env` nếu thiếu, khởi động database/Redmine, seed baseline rồi build MCP. Lần đầu cần mạng. Các tài khoản tổng hợp gồm admin, demo-manager, demo-developer, demo-reporter và mcp-reader; mật khẩu nằm trong `TEST_USER_PASSWORD`. Mật khẩu database và API key là dữ liệu riêng tư. Không chia sẻ output Compose đã resolve secret.

Để thao tác Compose trong Git Bash, tắt chuyển đổi đường dẫn Windows:

```bash
export MSYS_NO_PATHCONV=1
export MSYS2_ARG_CONV_EXCL='*'
docker compose -p redmine-mcp-test --env-file .env -f deploy/compose.yaml -f deploy/compose.test.yaml ps
docker compose -p redmine-mcp-test --env-file .env -f deploy/compose.yaml -f deploy/compose.test.yaml stop
```

`stop` giữ volume. Chạy lại `dev-up.sh` để khởi động; seed đã hoàn tất sẽ được bỏ qua. Trước khi chạy MCP local trên cổng 8000, dừng riêng service:

```bash
docker compose -p redmine-mcp-test --env-file .env -f deploy/compose.yaml -f deploy/compose.test.yaml stop mcp-server
```

## Seed và reset

```bash
bash scripts/seed.sh
bash scripts/seed-history.sh
```

Baseline đã hoàn tất được bỏ qua; baseline bị ngắt không tự resume. History có checkpoint để resume. History bổ sung 8 project, 20 user, 12 version, 300 issue và 900 time entry. Seed quản trị tách khỏi reader/writer MCP.

Chỉ reset môi trường tổng hợp riêng, có thể bỏ đi và có marker hợp lệ:

```bash
bash scripts/reset-test-env.sh --confirm-reset
```

Reset xóa database, file và local state của môi trường đó; backup được giữ. ID có thể đổi sau reset, nên luôn đọc manifest mới.

## Backup và restore

```bash
bash scripts/backup.sh baseline
bash scripts/restore.sh baseline
```

Tên snapshot dài tối đa 64 ký tự, bắt đầu bằng chữ hoặc số, chỉ dùng chữ, số, `_` và `-`. Backup không ghi đè snapshot có sẵn. Dump, attachment, manifest, credential và metadata image/version nằm trong `.local/backups/`, cần giữ riêng tư.

Backup dừng MCP và Redmine, cố gắng khởi động lại khi kết thúc hoặc lỗi. Snapshot thiếu completion marker không được restore. Restore thay database, file và local state; chỉ nhận snapshot tin cậy đúng phiên bản và marker. Thành công mới khởi động lại. Nếu restore lỗi, service được giữ dừng để tránh chạy dữ liệu khôi phục dở dang. Kiểm chứng checksum và recovery đầy đủ vẫn còn hoãn.

## Redmine bên ngoài

Môi trường tổng hợp ghim Redmine 7.0.2; helper từ chối volume thiếu label phiên bản phù hợp. Với Redmine ngoài, dùng file cấu hình riêng và base Compose, không dùng override tổng hợp:

```bash
docker compose -p redmine-mcp-external --env-file .local/external.env -f deploy/compose.yaml up -d --build
```

Không seed/reset/restore môi trường ngoài. Trên Windows, container có thể dùng `host.docker.internal` để kết nối dịch vụ host. Giữ TLS verification bật; HTTPS/OAuth hosting là phạm vi triển khai riêng.

## Writer riêng :id=separate-writer

Cấu hình `.local/writer.env` với API key cá nhân, admission và gate cho các operation cần thiết. Tài khoản thông thường vẫn phải có quyền Redmine gốc.

```bash
docker compose -p redmine-mcp-writer --env-file .local/writer.env -f deploy/compose.yaml --profile writer up -d --build mcp-writer
```

Writer bind localhost 8001; reader 8000 vẫn buộc read-only. Sau khi đổi environment, recreate container và refresh client/tool list; restart đơn thuần không nạp lại environment. Writer tổng hợp phải nối môi trường đã có marker, không tạo database tổng hợp thứ hai ngoài ý muốn.

CSV giới hạn operation cụ thể; `allowed_all` gồm cả các writer đăng ký sau này; danh sách trống bật 0 writer. Khi 5xx, timeout hoặc interruption, đối soát trạng thái thực tế trước khi thử lại. Giữ các item batch đã được chấp nhận; GET kiểm chứng thất bại không rollback mutation.

## Xử lý sự cố

| Triệu chứng | Hướng xử lý |
| --- | --- |
| Docker không sẵn sàng | Khởi động Docker Desktop và chọn Linux containers |
| Cổng bị chiếm | Dừng service trùng cổng trước khi chạy local |
| 401 hoặc không thấy tài nguyên | Kiểm tra API key Redmine và quyền tài khoản; token Inspector là token khác |
| TLS lỗi | Cấu hình CA tin cậy, giữ verification bật |
| Marker/version không phù hợp | Không bypass guard; xác định đúng môi trường và volume |
| Seed baseline bị ngắt | Sửa nguyên nhân; chỉ reset nếu môi trường dùng riêng có thể bỏ đi |
| Restore lỗi | Giữ service dừng và xử lý snapshot/dữ liệu trước khi chạy lại |

Health endpoint không chứng nhận upstream hoặc production readiness. Audit đầy đủ, metrics, CI và diễn tập rollback/recovery còn hoãn. Xem [bằng chứng danh mục](/vi/docs/testing/evidence/current-catalog-acceptance.md).
