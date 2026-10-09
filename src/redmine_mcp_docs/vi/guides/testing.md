# Kiểm thử và bằng chứng

Hướng dẫn này dành cho công việc xác minh được cho phép riêng. Đọc tài liệu hoặc chạy portal
không tự chạy test, chuẩn bị fixture, mở Inspector hay cho phép request trực tiếp.

## Ba lớp kiểm thử

| Lớp | Thư mục | Mục đích và môi trường |
| --- | --- | --- |
| Unit | `tests/unit/` | Model, policy và service dùng port giả |
| Integration offline | `tests/integration/` | Hợp đồng REST/MCP với Redmine mock và ASGI nội bộ |
| E2E trực tiếp | `tests/e2e/` | Kịch bản được chọn rõ ràng trên Redmine 7.0.2 cô lập, do bạn quản lý |

Pytest mặc định chỉ phát hiện hai lớp offline. E2E cần `--run-e2e`, fixture đúng phiên bản
do bạn quản lý và các bước chuẩn bị/tiếp nhận đã ghi trong tài liệu.
Không thay bằng Redmine dùng chung hoặc môi trường khách hàng thật.

## Lệnh cho công việc được phép kiểm thử

Chạy từ thư mục gốc repository trong Git Bash:

```bash
uv run --frozen pytest tests/unit
uv run --frozen pytest tests/integration
uv run --frozen pytest
```

Chuẩn bị E2E tạo tài nguyên và cần được cho phép riêng:

```bash
uv run --frozen python scripts/prepare-e2e.py
uv run --frozen pytest tests/e2e --run-e2e
```

Xem [lộ trình kiểm thử](/vi/docs/testing-roadmap.md) về dependency/fixture, trách nhiệm
dọn dẹp, xác minh bổ sung và phạm vi thực hiện. Input Inspector và kết quả mong đợi nằm trong
[xác minh thủ công](/vi/docs/manual-verification.md).

## Đọc bằng chứng hiện có

Bằng chứng gắn với revision, môi trường, tập kịch bản và ngày đã ghi nhận.
Số test pass trong lịch sử không xác minh working tree mới hoặc tự đóng phần nghiệm thu đang chờ.

Đọc cùng [tổng hợp task](/vi/docs/plans/index.md),
[ma trận coverage](/vi/docs/plans/testing-coverage.md) và
[sổ nghiệm thu danh mục](/vi/docs/testing/evidence/current-catalog-acceptance.md).
Các thay đổi preparation, retry và time entry sau đó có bằng chứng riêng trong sidebar.
Nghiệm thu tạo time entry vẫn đang chờ; kiểm thử discovery activity đã được miễn trong baseline
đã ghi nhận. Theo lộ trình gốc để biết các cập nhật tiếp theo.

Ngưỡng coverage, CI kiểm thử và mức sẵn sàng vận hành/khôi phục rộng hơn vẫn được hoãn.
Portal giữ bằng chứng hiện có, không công bố kết quả nghiệm thu mới.

## Kiểm tra portal riêng

[Checklist portal](verification.md) bao gồm asset offline, điều hướng, sơ đồ, ranh giới xuất
và static hosting; không cần credential Redmine hay fixture test. Xem phạm vi đã thực hiện
trong [bản rà soát giao diện ngày 2026-10-09](layout-review.md).
Bản tiếng Việt, lựa chọn giao diện và sidebar kéo đổi độ rộng chưa được kiểm tra trình duyệt
trong các lần triển khai chức năng đó.
