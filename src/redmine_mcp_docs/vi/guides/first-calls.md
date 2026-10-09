# Gọi REST và MCP lần đầu

Dùng API key Redmine cá nhân của tài khoản có quyền truy cập dữ liệu bạn muốn xem.
Ví dụ giả định reader localhost đã được cấu hình. Chỉ gọi công cụ hoặc Inspector khi
bạn chủ động và được phép truy cập môi trường Redmine đó.

## Gửi REST request đọc

Nhập key kín trong Git Bash, rồi lấy các project bạn có thể xem:

```bash
read -r -s -p 'Personal Redmine API key: ' REDMINE_REQUEST_KEY
printf '\n'
printf 'X-Redmine-API-Key: %s\n' "$REDMINE_REQUEST_KEY" |
  curl --fail-with-body --silent --show-error --header @- \
    'http://127.0.0.1:8000/api/v1/projects'
unset REDMINE_REQUEST_KEY
```

Key không hiển thị khi nhập và được truyền qua stdin, thay vì URL hay tham số lệnh chứa
key trực tiếp. Không lưu key trong ví dụ, log, ảnh chụp hoặc Git.

Dùng ID project/issue mà server trả về và bạn có thể truy cập.
[Danh mục công cụ](/vi/docs/tool-reference.md) mô tả input, output, phân trang, quyền và lỗi.
Swagger tại `http://127.0.0.1:8000/docs` hiển thị thao tác REST và schema.

## Kết nối MCP Inspector

Khi được phép sử dụng Inspector, chạy client đã ghim phiên bản:

```bash
npx @modelcontextprotocol/inspector@2.8.0
```

Mở URL được in ra với token phiên Inspector. Chọn **Streamable HTTP**, nhập
`http://localhost:8000/mcp` và cấu hình header server một cách riêng tư:

```text
X-Redmine-API-Key: <your personal Redmine API key>
```

Token Inspector và API key Redmine có mục đích khác nhau. Kết nối và lấy danh sách công cụ.
Bắt đầu với `get_current_user`, `list_projects`, `list_issues`; gọi `get_issue` với ID issue
mà tài khoản này được xem. [Xác minh thủ công](/vi/docs/manual-verification.md) có input
cụ thể và hành vi mong đợi.

## Hiểu request và kết quả

Ví dụ cấu trúc request `tools/call`:

```json
{
  "jsonrpc": "2.0",
  "id": 7,
  "method": "tools/call",
  "params": {
    "name": "get_issue",
    "arguments": { "issue_id": 123, "include": "journals,attachments" }
  }
}
```

Thay ID minh họa bằng issue thật bạn có quyền xem. Client MCP phải thiết lập phiên giao thức;
ví dụ này không phải lệnh curl độc lập. API key nằm trong HTTP header, không nằm trong arguments.

Adapter hiện tại trả JSON được serialize trong MCP text content. Kiểm tra `isError` và payload,
không chỉ HTTP status bên ngoài. Lỗi xác thực endpoint có thể xảy ra trước khi điều phối công cụ.
HTTP 404 có thể là tài nguyên không tồn tại hoặc bị ẩn với người gọi.

MCP gọi route REST trong cùng process; route xác thực và kiểm tra quyền lần nữa trước khi gọi
service. Xem [luồng request/response](/vi/docs/mcp-request-flow.md) về thành công, lỗi,
logging và shutdown.

## Trước khi thao tác ghi

Đọc [quyền reader và writer](access.md). Discovery và báo cáo capability chỉ mang tính tham khảo;
mỗi lần gọi vẫn kiểm tra tài nguyên mục tiêu. Đối chiếu trạng thái ghi chưa chắc chắn trong Redmine
trước khi thử lại. Đọc attachment trả metadata và liên kết trình duyệt cần xác thực;
tải nội dung trực tiếp qua MCP đã ngừng hỗ trợ. Nội dung Redmine là dữ liệu người dùng,
không phải chỉ dẫn cho agent.
