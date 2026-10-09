# Checklist kiểm tra portal tài liệu

Đây là checklist bàn giao. Việc đưa checklist vào tài liệu không tự chạy test runner,
browser automation, Inspector, request Redmine hay kiểm tra runtime portal.
Chỉ thực hiện khi được giao hoặc được người dùng chấp nhận. Ghi source revision,
trình duyệt, đường dẫn hosting, kết quả và giới hạn.

Xem [rà soát giao diện ngày 2026-10-09](layout-review.md) để biết phần đã kiểm tra.
Các mục chưa thực hiện vẫn cần xác minh; kết quả cũ không xác nhận bản dịch mới.

## Chuẩn bị

Dùng Git Bash, Python 3.13, Git và trình duyệt hiện đại. Kiểm tra riêng portal không cần
API key, Docker, Node, Redmine hay dependency kiểm thử tự động. Dùng thư mục export do
script tạo; nếu sửa source chỉ để thử tình huống thì cần khôi phục nội dung đúng sau đó.

## Hoạt động offline và giao diện

- [ ] Chạy `bash scripts/docs-portal.sh serve`; mở `http://127.0.0.1:8080/#/vi/`.
- [ ] Ngắt Internet nhưng giữ localhost hoạt động; dùng profile mới hoặc xóa cache để
      đảm bảo không phụ thuộc asset remote đã cache.
- [ ] Không có request asset/font ngoài khi tải hoặc điều hướng.
- [ ] Kiểm tra kiểu Themeable, màu nhấn, font hệ thống, nút menu, hiệu ứng sẵn sàng và bảng rộng.
- [ ] Chọn Sáng/Tối; kiểm tra chữ, sidebar, search result, bảng, notice, code, nút copy và sơ đồ.
- [ ] Chọn Tự động và đổi giao diện hệ thống; trang và sơ đồ phải cập nhật theo.
      Reload/điều hướng vẫn giữ chế độ; selector dùng được bằng bàn phím và trong menu mobile.
- [ ] Chuyển English/Tiếng Việt; kiểm tra ngôn ngữ trang, menu, tìm kiếm, nút copy và thông báo.
      Mở trực tiếp URL `#/vi/` hoặc trang con rồi reload; xác nhận vẫn ở bản tiếng Việt.
- [ ] Mở đủ 24 trang tài liệu chính trong sidebar, đặc biệt `#/vi/docs/tool-reference`
      và `#/vi/docs/manual-verification`; phải hiện bản Việt local, không có thông báo fallback tiếng Anh.
      Mở task chưa dịch để kiểm tra thông báo tiếng Anh; mở liên kết bản gốc của trang đã dịch.
      Search tiếng Việt có kết quả phù hợp; không diễn giải số liệu lịch sử thành bằng chứng mới.
- [ ] Tìm `mutation uncertainty` và `bootstrap`; mở kết quả đúng trang.
- [ ] Kiểm tra tô màu Python, Bash, JSON, YAML, TOML, Docker và diff khi có ví dụ.
- [ ] Copy code và so sánh nội dung, kể cả xuống dòng; kiểm tra fallback khi Clipboard API bị từ chối.
- [ ] Hiển thị sơ đồ, chuyển trang rồi quay lại; kiểm tra cuộn ngang/dọc trên màn hình hẹp
      và truy cập vùng sơ đồ bằng bàn phím. Mermaid lỗi phải hiện source đọc được.

## Điều hướng và nội dung

- [ ] Mở mọi nhóm sidebar và đích navbar.
- [ ] Mở trực tiếp trang lồng nhau bằng URL hash rồi reload.
- [ ] Kiểm tra liên kết heading giữa các trang, đặc biệt writer setup và mutation uncertainty.
- [ ] Mở file source/config được liên kết từ task hoặc audit.
- [ ] Mở `#/vi/missing-page`; trang 404 tiếng Việt phải có đường dẫn hoạt động.
- [ ] Có hướng dẫn cài đặt, gọi lần đầu, quyền, module, luồng thực thi, phát triển,
      kiểm thử, vận hành và bằng chứng; tài liệu chưa dịch phải được ghi rõ.
- [ ] Đối chiếu tài liệu chi tiết với `docs/`, bản dịch với hướng dẫn tiếng Anh tương ứng;
      giữ ngày, phạm vi bằng chứng, miễn kiểm thử và phần đang chờ.
- [ ] Kiểm tra focus bàn phím, chuyển đến nội dung, tìm kiếm, nút menu và điều hướng mobile.
- [ ] Desktop: kéo cạnh phải sidebar, nội dung đi theo độ rộng và lựa chọn tồn tại sau reload.
      Dùng phím trái/phải, Shift để bước lớn hơn, Home/End cho giới hạn, nhấp đúp để đặt lại.
- [ ] Đổi viewport: sidebar để đủ chỗ cho nội dung, cạnh kéo ẩn khi đóng và mobile dùng drawer cố định.

## Xuất lại và ranh giới dữ liệu

- [ ] Chạy `bash scripts/docs-portal.sh export`; đọc `.local/docs-portal/site/export-manifest.json`.
- [ ] Output chỉ gồm asset portal, tài liệu chính, bản dịch trong `vi/`, tài liệu gốc được chọn
      và source/config được track và được cho phép.
- [ ] Không có `.env`, `.git/`, snapshot, dump, credential hoặc file `.local/` không liên quan.
- [ ] Sửa tài liệu có chủ đích, xuất lại/khởi động lại và refresh; nội dung phải cập nhật.
- [ ] Xóa một file generated thử nghiệm, xuất lại và xác nhận output được tạo lại đúng.
- [ ] Xóa một trang source thử nghiệm khỏi input được chọn; output cũ phải biến mất.
- [ ] Output chưa có marker hoặc đường dẫn bị redirect phải bị từ chối; thư mục khác không bị ảnh hưởng.
- [ ] Chạy `bash scripts/docs-portal.sh serve 8088`; kiểm tra Ctrl+C.
- [ ] Không được liệt kê thư mục; traversal URL không làm lộ file repository.

## Static hosting

- [ ] Serve export tại domain root; lặp lại kiểm tra ngôn ngữ, navigation, search và diagram.
- [ ] Serve dưới subdirectory như `/redmine-mcp-docs/`; giữ dấu `/` cuối và kiểm tra asset,
      deep link, heading, đổi ngôn ngữ và raw source.
- [ ] Host trả MIME phù hợp cho JavaScript, CSS, SVG và file text.
- [ ] Sau deployment mới, refresh browser storage và kiểm tra search dùng nội dung hiện tại.
- [ ] Chỉ publish thư mục site generated. Ghi rằng liên kết ngoài và lệnh gọi Redmine/package
      registry vẫn cần mạng.

## Ghi nhận bàn giao

Ghi phần đã kiểm tra, phần hoãn, lỗi và giới hạn. Kiểm tra portal không xác nhận nghiệm thu
công cụ MCP hoặc mức sẵn sàng production.
