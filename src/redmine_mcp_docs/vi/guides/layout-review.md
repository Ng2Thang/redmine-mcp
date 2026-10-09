# Rà soát giao diện portal

Ngày rà soát: **2026-10-09**. Người dùng yêu cầu kiểm tra layout, CSS và lỗi sau khi triển khai
Docsify Themeable. Kết quả áp dụng cho những trang được lấy mẫu tại working tree lúc đó,
không phải mọi mục trong [checklist](verification.md), và không xác minh bản tiếng Việt mới.

## Những điểm đã sửa

- Khôi phục viền đầy đủ của card trang chủ bị style liên kết ghi đè.
- Cho nhãn sidebar dài xuống dòng thay vì bị cắt.
- Thay ba dấu chấm phẩy trong nội dung message của sequence diagram: Mermaid đã coi chúng
  là ký hiệu kết thúc câu lệnh và không render được.
- Giới hạn sơ đồ lớn trong vùng cuộn, thêm chú thích/focus bàn phím và bỏ giới hạn chiều cao khi in.
- Tránh nút copy trùng, thông báo trạng thái copy, khôi phục focus sau fallback và chọn code khi copy lỗi.
- Dọn container lỗi Mermaid tạm khi chuyển sang hiển thị source.

## Kết quả đã quan sát

Dùng Microsoft Edge headless với profile mới, phục vụ export qua localhost, tắt cache và chặn
HTTP request ra ngoài. Viewport desktop là 1440 pixel; mobile là 390 và 320 pixel.

- Các trang lấy mẫu: home, installation, first calls, configuration, execution flow, module map
  và audit không tràn ngang toàn trang.
- Menu mobile mở được, nhãn dài đọc được.
- Hai sơ đồ execution flow và một sơ đồ module map render, không fallback.
- Search `mutation uncertainty` trả kết quả liên quan.
- Liên kết heading cấu hình đến đúng đích; cả 12 raw source link lấy mẫu trả HTTP 200.
- Các code block có nút copy. Click thật copy đúng nội dung sau khi chuẩn hóa xuống dòng;
  Windows chuyển LF thành CRLF.
- Route cố ý không tồn tại hiện trang 404 riêng. HTTP 404 dự kiến của route này là request
  lỗi duy nhất trong lượt điều hướng đó.
- Không quan sát thấy exception JavaScript chưa xử lý hoặc request asset ra ngoài.

Screenshot và JSON observations nằm trong `.local/docs-portal-review/`, được ignore và không
deploy cùng portal. Bản ghi tiếng Anh tại `guides/layout-review.md` giữ nguyên nguồn bằng chứng.

## Giới hạn

Đây là kiểm tra lấy mẫu trong một trình duyệt headless. Chưa xác minh Firefox, Safari,
thiết bị cảm ứng thật, mọi đích điều hướng, mọi ngôn ngữ tô màu, từ chối Clipboard API,
fallback sơ đồ lỗi, print, domain công khai hoặc subdirectory hosting.
Các tình huống xóa khi export và ranh giới bảo mật vẫn trong checklist.
Không chạy unit, integration, E2E, Inspector hoặc request Redmine trực tiếp.

Sidebar đổi độ rộng, chế độ Sáng/Tối/Tự động và bản tiếng Việt được thêm sau lượt rà soát
này; không coi kết quả trên là xác minh các chức năng đó.
