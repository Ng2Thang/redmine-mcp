<p class="portal-eyebrow">Tài liệu / Redmine MCP</p>

# Hiểu server. Sử dụng công cụ. Theo dõi luồng xử lý.

Redmine MCP cung cấp thao tác Redmine qua REST và MCP, xác thực bằng API key cá nhân.
Bắt đầu với cài đặt, kết nối client, rồi tìm hiểu kiến trúc và quy trình phát triển.

<div class="portal-grid">
  <a class="portal-card" href="#/vi/guides/installation"><strong>Bắt đầu</strong><span>Chọn Docker hoặc Python local và chuẩn bị môi trường.</span></a>
  <a class="portal-card" href="#/vi/guides/first-calls"><strong>Sử dụng công cụ</strong><span>Gửi REST request đầu tiên và kết nối MCP Inspector.</span></a>
  <a class="portal-card" href="#/vi/guides/module-map"><strong>Theo dõi thực thi</strong><span>Tìm hiểu xác thực, điều phối, truy cập Redmine và trả kết quả.</span></a>
  <a class="portal-card" href="#/vi/guides/testing"><strong>Tìm hiểu kiểm thử</strong><span>Ba lớp kiểm thử, bằng chứng và điều kiện cho phép thực hiện.</span></a>
</div>

## Chọn lộ trình đọc

| Nhu cầu | Bắt đầu tại | Đọc tiếp |
| --- | --- | --- |
| Cài đặt và kết nối | [Cài đặt](guides/installation.md) | [Gọi lần đầu](guides/first-calls.md) |
| Cấu hình quyền | [Reader và writer](guides/access.md) | [Cấu hình](/vi/docs/configuration.md) |
| Tìm tham số và kết quả | [Danh mục công cụ](/vi/docs/tool-reference.md) | [Xác minh thủ công](/vi/docs/manual-verification.md) |
| Hiểu triển khai | [Các module](guides/module-map.md) | [Kiến trúc](/vi/docs/architecture.md), [luồng thực thi](/vi/docs/mcp-request-flow.md) |
| Thêm hoặc sửa công cụ | [Phát triển](/vi/docs/development.md) | [Quy trình công cụ](/vi/docs/workflows/redmine-tools.md) |
| Vận hành môi trường | [Vận hành](/vi/docs/operations.md) | [Dữ liệu tổng hợp](/vi/docs/test-data.md) |
| Đánh giá nghiệm thu | [Tổng quan kiểm thử](guides/testing.md) | [Ma trận coverage](/vi/docs/plans/testing-coverage.md), [lộ trình](/vi/docs/plans/index.md) |

## Phạm vi hiện tại

Danh mục đã đăng ký gồm **18 thao tác đọc và 18 thao tác ghi**. Reader mặc định chỉ đọc;
thao tác ghi cần writer riêng được bật rõ ràng, danh sách thao tác được cho phép,
API key Redmine cá nhân, điều kiện tiếp nhận người gọi và quyền gốc trong Redmine.
Phiên bản Redmine mục tiêu là **7.0.2**.

Đây là bản triển khai phát triển để đánh giá pilot. Bằng chứng kiểm thử chỉ áp dụng cho
revision, ngày và kịch bản đã ghi nhận. Xem [lộ trình hiện tại](/vi/docs/plans/index.md)
để biết phần nghiệm thu còn chờ và những bước đã được miễn; portal không bổ sung chứng nhận production.

## Ngôn ngữ và giao diện

Dùng **Ngôn ngữ** trong sidebar để chuyển giữa English và Tiếng Việt. Dùng **Giao diện**
để chọn Sáng, Tối hoặc Tự động theo hệ thống. Trên desktop, kéo cạnh phải của sidebar
để thay đổi độ rộng; nhấp đúp để đặt lại. Trên mobile, mở menu để thấy các lựa chọn này.

Bản tiếng Việt gồm giao diện, trang chủ, hướng dẫn nhập môn và 24 trang tài liệu chính
trong menu. Các hồ sơ dài được biên tập thành bản tổng hợp, có liên kết tới bản tiếng Anh
đầy đủ. Task chưa dịch dùng tài liệu tiếng Anh và có thông báo. Giữ nguyên ngày, trạng thái
chờ và giới hạn xác minh. Source chuẩn vẫn ở `docs/`; bản dịch được duy trì tại
`src/redmine_mcp_docs/vi/` và cần cập nhật cùng bản tiếng Anh tương ứng.

Hiển thị, sơ đồ, tô màu mã và tìm kiếm dùng asset local. Liên kết ngoài và lệnh cài package
hoặc truy cập Redmine vẫn cần kết nối mạng. Xem [bảo trì và hosting](/vi/docs/documentation-portal.md)
và [checklist portal](guides/verification.md).
