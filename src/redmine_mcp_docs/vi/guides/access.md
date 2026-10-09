# Quyền truy cập reader và writer

Mỗi người gọi dùng API key Redmine cá nhân. Redmine chịu trách nhiệm cho quyền gốc với
project, issue, attachment, membership và time entry.

## So sánh deployment

| Hành vi | Reader mặc định | Writer riêng, bật chủ động |
| --- | --- | --- |
| Cổng local mặc định | `8000` | `8001` |
| Thao tác đọc | 18 thao tác đọc đã đăng ký | Danh mục đọc cùng các thao tác ghi được cấu hình |
| Tiếp nhận thao tác thay đổi | Tắt | Cần bật rõ ràng và cấu hình operation gates |
| Danh tính người gọi | API key Redmine cá nhân | Chế độ tiếp nhận pinned-key hoặc personal-key |
| Quyền tài nguyên mục tiêu | Quyền xem gốc trong Redmine | Quyền gốc và kiểm tra của writer |

Danh mục ghi đầy đủ có 18 thao tác. Một writer có thể công bố ít hơn tùy cấu hình và
discovery theo người gọi.

## Cấu hình writer

Theo [deployment writer riêng](/vi/docs/configuration.md#separate-writer-deployment)
và [vận hành writer](/vi/docs/operations.md#separate-writer).
Dùng file môi trường riêng tư và listener riêng. Quy trình writer không bật ghi trên reader.

Cần `REDMINE_WRITE_ENABLED=true` và danh sách thao tác được cấu hình. Chế độ `pinned_key`
cần thêm digest key riêng tư và ID người dùng được tiếp nhận. `personal_key` xác thực từng
người gọi độc lập và có thể giới hạn theo ID người dùng. Cấu hình operation rỗng không cho phép ghi.

Danh sách operation rõ ràng giới hạn các thao tác được phép. Giá trị độc lập `allowed_all`
cho phép mọi thao tác ghi đã đăng ký, kể cả đăng ký mới sau nâng cấp. Chọn có chủ đích và
tạo lại hoặc khởi động lại writer theo tài liệu khi đổi cấu hình.

## Discovery không cấp quyền

Discovery personal-key dựa trên project có thể xem và bằng chứng membership/role được thu thập
trong giới hạn của request. Công cụ được liệt kê vẫn có thể có điều kiện hoặc chưa rõ quyền
với một tài nguyên cụ thể. Báo cáo capability chỉ để tham khảo; lúc gọi vẫn kiểm tra deployment
gates, điều kiện tiếp nhận người gọi, khả năng xem mục tiêu và quyền gốc.

## Xử lý kết quả thao tác ghi

Thao tác ghi chỉ được gửi một lần. Receipt phân biệt việc được chấp nhận, kết quả chưa chắc chắn
và quan sát đọc lại sau đó. Transport thành công không tự chứng minh mọi trường yêu cầu đều đổi.
Không tìm thấy tài nguyên khi đọc lại không chứng minh thao tác xóa chưa chắc chắn đã commit.
Kiểm tra trạng thái gốc trước khi quyết định thử lại.

Đọc [mutation uncertainty](/vi/docs/tool-reference.md#mutation-uncertainty) và hợp đồng
từng operation trước khi thay đổi. Quản trị dữ liệu tổng hợp, dọn fixture và truy cập database
tách biệt với công cụ MCP.
