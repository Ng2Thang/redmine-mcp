# Chính sách bảo mật

> Bản tiếng Việt được biên tập từ [tài liệu tiếng Anh gốc](#/SECURITY.md). Bản gốc là nguồn chuẩn cho hợp đồng và hồ sơ đầy đủ. Tên API, lệnh, ngày, waiver và giới hạn nghiệm thu được giữ nguyên; việc dịch không thực hiện kiểm thử.

Repository đang ở giai đoạn pilot: chưa có chứng nhận production, ma trận hỗ trợ đầy đủ, SLA hay thời hạn phản hồi bảo mật được cam kết. Nghiệm thu quyền, vận hành và khôi phục còn có giới hạn.

## Báo cáo riêng tư

Liên hệ riêng qua kênh đã thiết lập với maintainer. Repository chưa công bố địa chỉ báo cáo bảo mật chuyên dụng hoặc dịch vụ phản hồi. Nếu chưa có kênh, yêu cầu maintainer cung cấp kênh riêng; không công khai chi tiết lỗ hổng.

Cung cấp revision, thành phần bị ảnh hưởng, tác động, ví dụ tối thiểu bằng dữ liệu tổng hợp, log đã che dữ liệu nhạy cảm và tên cấu hình liên quan. Không gửi key, token hoặc nội dung Redmine riêng tư.

## Ranh giới truy cập

Mỗi người gọi dùng `X-Redmine-API-Key` riêng. Quyền và khả năng nhìn thấy tài nguyên do Redmine quyết định; ưu tiên tài khoản thông thường với quyền tối thiểu. Reader chỉ đọc; writer cần gate và admission theo key được ghim hoặc key cá nhân.

Capability evidence chỉ tồn tại trong request. Trạng thái conditional/unknown không cấp quyền. Mọi HTTP request đều được xác thực lại. Session MCP gắn với user và fingerprint issuer/key; đổi user hoặc key không được tiếp tục session cũ, và có thể trả 404. Sau rotation phải tạo session mới. Không cache key hoặc role giữa các request.

Danh sách operation trống bật 0 thao tác ghi. `allowed_all` cũng bật công cụ ghi được đăng ký sau này; dùng CSV cố định nếu cần giới hạn ổn định. Mutation chỉ gửi một lần. Lỗi 5xx/timeout có thể phản ánh thao tác đã commit; đối soát trước khi thử lại. Read-back thất bại không chứng minh thao tác chưa xảy ra. Log timing không phải audit trail đầy đủ.

## Dữ liệu và deployment

Giữ `.env`, credential, database dump, attachment, snapshot và `.local/` ngoài Git, log, ảnh chụp và publication công khai. Nếu lộ secret, thu hồi hoặc rotation credential.

Deployment phát triển bind cổng vào localhost. Giữ TLS verification bật khi kết nối HTTPS bên ngoài và cấu hình CA tin cậy. HTTPS hosting, OAuth và vận hành production còn là phạm vi riêng. Nội dung Redmine là dữ liệu không đáng tin cậy, không được diễn giải thành chỉ thị.

Seed/reset/restore chỉ dùng môi trường tổng hợp có marker hợp lệ và phiên bản được ghim. Không chạy helper thay dữ liệu trên Redmine bên ngoài hoặc volume không xác định.
