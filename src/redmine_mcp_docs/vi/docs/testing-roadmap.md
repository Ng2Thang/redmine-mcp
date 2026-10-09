# Lộ trình kiểm thử

> Bản tiếng Việt được biên tập từ [tài liệu tiếng Anh gốc](#/docs/testing-roadmap.md). Bản gốc là nguồn chuẩn cho hợp đồng và hồ sơ đầy đủ. Tên API, lệnh, ngày, waiver và giới hạn nghiệm thu được giữ nguyên; việc dịch không thực hiện kiểm thử.

## Trạng thái hiện tại

Danh mục đã đăng ký gồm 18 đọc/18 ghi. Nghiệm thu là kết quả theo revision, ngày và phạm vi cụ thể; không chứng nhận production hoặc mọi tổ hợp quyền.

| Hồ sơ | Kết quả được ghi nhận | Giới hạn còn lại |
| --- | --- | --- |
| PREP-020, 2026-10-07 | 1.086 offline, 21 live trên Redmine 7.0.2 thuộc sở hữu; Inspector pass | Danh mục lúc đó là 17 đọc/15 ghi; khoảng trống H1–H6 còn trong ledger |
| PREP-022–026 | 1.395 offline, 23 owned live; Inspector pass | CI, ngưỡng coverage, recovery và production readiness hoãn |
| PREP-027 | Retry được kiểm tra offline và bằng reader/Inspector riêng | Live không thực hiện mutation; không mô phỏng mọi lỗi mạng native |
| TOOL-040 | Người dùng miễn kiểm thử | Không tuyên bố runtime acceptance |
| TOOL-041 | Đã triển khai | Kiểm thử còn pending |
| TOOL-042 | 61 unit, 99 integration riêng, 10 owned native/Inspector | Full run ghi 1.755 pass và 1 lỗi catalog cũ; rerun sửa lỗi và 7 case muộn pass, chưa có full run cuối sạch |
| TOOL-043 | 32 unit, 82 integration riêng, 1.889 full offline pass | 12 owned native/Inspector case qua 11 + 1 lần chạy; không có một lần cuối chạy cả 12 |

Đọc [ledger](/vi/docs/testing/evidence/current-catalog-acceptance.md) và từng trang bằng chứng để xem revision, cleanup và giới hạn chính xác. PREP-021 là cập nhật tài liệu, không thực thi xác minh.

## Ba lớp kiểm thử

**Unit** kiểm tra validation, service, policy, auth và budget bằng fixture offline. **Integration** kiểm tra gateway, REST và MCP SDK qua transport giả lập, không gọi Redmine thật. **Live E2E** chỉ chạy khi được chọn rõ ràng và được assignment cho phép, trên môi trường tổng hợp thuộc sở hữu được ghim Redmine 7.0.2.

```bash
uv run pytest
uv run pytest tests/unit
uv run pytest tests/integration
uv run python scripts/prepare-e2e.py
uv run pytest tests/e2e --run-e2e
uv run python scripts/verify-e2e-supplement.py
```

Đây là lệnh bàn giao, không phải chỉ thị tự chạy. Discovery mặc định offline; fixture tắt đọc `.env`, xóa cấu hình runtime và chặn HTTP thật. Chọn `tests/e2e` thiếu `--run-e2e` bị từ chối trước fixture. Helper dùng chung không phải test module được collect.

## Môi trường live thuộc sở hữu

Môi trường `redmine-mcp-e2e` dùng cổng 3001, database/file volume riêng và label phiên bản. Không dùng Redmine 6.0.5 chung ở cổng 3000 cho nghiệm thu 7.0.2. Preflight xác minh image được ghim, marker, volume, key riêng tư và fixture native. Admin chỉ chuẩn bị fixture; MCP vẫn dùng người gọi thông thường và không truy cập database trực tiếp.

Preparation tạo tài nguyên và không phải thao tác read-only. Key nằm trong file ignored, không truyền trên command line. Read-back đối chiếu cả field được chấp nhận và field bị bỏ qua; mutation không chắc chắn cần reconciliation. Cleanup chỉ tác động tài nguyên thuộc sở hữu; history native có thể còn lại. Không reset môi trường dùng chung.

Supplement dùng app localhost tạm ở cổng 18081, Inspector 2.8.0 và Edge để kiểm tra discovery/read, liên kết attachment metadata và xác thực download trong trình duyệt. Sau đó dừng app/browser và xóa attachment thuộc sở hữu. Profile và cấu hình riêng tư nằm trong `.local/`.

```bash
uv run uvicorn tests.e2e.server:create_app --factory --host 127.0.0.1 --port 18081
npx @modelcontextprotocol/inspector@2.8.0
```

Chỉ thực hiện khi được cấp phạm vi kiểm thử tương ứng.

## Các lớp bảo vệ cần kiểm chứng

Key khác nhau không bị lẫn giữa request. Header thiếu, trống hoặc lặp bị từ chối 401; identity upstream sai dạng trả 502, timeout 504, lỗi transport 502 và key bị thu hồi 401. Key không xuất hiện trong tool argument hoặc error. Reader giữ read-only và visibility theo người gọi.

Backlog gồm validation, mapping/TLS/timeout/key isolation, schema/error/shutdown MCP, role/private-resource filtering, seed resume, backup/restore trên volume mới, checksum/failure recovery và packaging/CI. Một phần đã có bằng chứng được chọn; backlog không có nghĩa mọi mục hoàn toàn chưa được kiểm tra. Ngưỡng coverage, CI kiểm thử và vận hành production vẫn hoãn. Xem [ma trận coverage](/vi/docs/plans/testing-coverage.md).

## Phụ lục ví dụ nguyên văn

Các đoạn mã/lệnh sau giữ nguyên từ bản gốc để tra cứu cú pháp. Không thực thi tự động; chỉ chạy bước kiểm thử hoặc mutation khi assignment cho phép.

```bash
uv run --frozen pytest tests/unit
uv run --frozen pytest tests/integration
uv run --frozen pytest
bash scripts/check.sh
```

```bash
uv run --frozen python scripts/prepare-e2e.py
uv run --frozen pytest tests/e2e --run-e2e
uv run --frozen python scripts/verify-e2e-supplement.py
```

```bash
uv run --frozen uvicorn tests.e2e.server:create_app --factory --host 127.0.0.1 --port 18081
npx @modelcontextprotocol/inspector@2.8.0
```

```bash
uv run --frozen pytest
```
