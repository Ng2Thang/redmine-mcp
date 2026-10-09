# Bảo trì và hosting documentation portal

> Bản tiếng Việt được biên tập từ [tài liệu tiếng Anh gốc](#/docs/documentation-portal.md). Bản gốc là nguồn chuẩn cho hợp đồng và hồ sơ đầy đủ. Tên API, lệnh, ngày, waiver và giới hạn nghiệm thu được giữ nguyên; việc dịch không thực hiện kiểm thử.

Portal Docsify chạy riêng với MCP và Swagger. Mặc định portal ở `http://127.0.0.1:8080/`; Swagger vẫn ở `/docs` trên server MCP.

## Export và serve

Dùng Git Bash từ repository root, với Git và Python 3.13 trên PATH. Portal không cần Docker, Node.js, dependency Python, kết nối Redmine hay API key.

```bash
bash scripts/docs-portal.sh export
bash scripts/docs-portal.sh serve
bash scripts/docs-portal.sh serve 8088
```

`export` tạo `.local/docs-portal/site/`. `serve` export trước rồi chạy HTTP server foreground bind `127.0.0.1`. Dừng bằng Ctrl+C và khởi động lại sau khi sửa tài liệu. Export thay output/staging có marker trong thư mục đã resolve; từ chối thư mục không có marker hoặc đường dẫn symlink/junction.

Exporter đọc nội dung working tree của tài liệu tracked và portal source được chọn rõ ràng. Tài liệu canonical mới dưới `docs/` cần được add vào Git. `export-manifest.json` liệt kê tài liệu và reference; HEAD trong manifest không chứng nhận nội dung chưa commit hoặc kết quả kiểm thử.

## Chỉnh sửa ở đâu

| Nội dung | Source |
| --- | --- |
| Hợp đồng kỹ thuật và hồ sơ chuẩn tiếng Anh | `docs/` và README gốc |
| Guide giới thiệu tiếng Anh | `src/redmine_mcp_docs/guides/` |
| Bản tiếng Việt, sidebar/navbar tiếng Việt | `src/redmine_mcp_docs/vi/` |
| Registry trang đã dịch và thông điệp giao diện | `assets/language.js` |
| Layout, routing, Mermaid, copy và resize | `assets/portal.css`, `assets/portal.js` |
| Sáng/tối/tự động | `assets/theme.js` |
| Export allowlist và server | `tools/portal.py` |

Không sửa generated output trong `.local/`. Giữ đường dẫn tương đối và anchor. Source/config reference chỉ được copy nếu tracked và thuộc allowlist, mở trực tiếp như file. Khi thêm bản dịch chi tiết, đăng ký route trong `language.js`; alias local được ưu tiên trước fallback tiếng Anh. Cập nhật sidebar để search tìm thấy trang.

## Ngôn ngữ và offline assets

Chọn **Ngôn ngữ → Tiếng Việt** hoặc mở `#/vi/`. Interface, guide và 24 trang tài liệu chính trong sidebar có bản tiếng Việt. Các bản chi tiết được biên tập lại theo chủ đề; bản tiếng Anh vẫn là nguồn chuẩn cho ledger đầy đủ, commit và scenario. Tên API, command và số liệu lịch sử giữ nguyên. Task chưa dịch dùng source tiếng Anh và có thông báo.

Khi canonical thay đổi, cập nhật bản Việt tương ứng và giữ ngày, waiver, pending acceptance, giới hạn verification. Đổi ngôn ngữ giữ route trang nhưng bỏ heading query; search cache tách theo ngôn ngữ, theme/sidebar width dùng chung.

Assets local gồm Docsify 4.13.1, search, Themeable 0.9.0, Mermaid 11.12.0 và Prism 1.29.0, cùng license/manifest. Theme Simple light có override dark, system fonts và không tải emoji. Giao diện sáng/tối/tự động được lưu theo hosting path; tự động theo hệ thống và Mermaid render lại khi theme đổi. Resize sidebar desktop lưu width; mobile dùng navigation riêng.

Export/serve không tải dependency. Rendering/search/highlight/diagram thiết kế hoạt động offline qua HTTP với JavaScript bật; không mở trực tiếp `index.html` bằng file URL. Reference bên ngoài và lệnh cài đặt Redmine/Inspector có thể cần mạng.

Chỉ trong maintenance được chọn rõ ràng mới tải lại package ghim:

```bash
python src/redmine_mcp_docs/tools/vendor_assets.py
```

Lệnh này liên hệ npm/upstream license, kiểm tra integrity và cập nhật assets/metadata. Review license và asset trước commit; đổi version là quyết định riêng.

## Static hosting

Export rồi upload **chỉ nội dung** `.local/docs-portal/site/`, giữ cấu trúc thư mục và `.nojekyll`. Host cần index directory và MIME type phù hợp. Hash routing không cần SPA rewrite. Root và subdirectory dùng asset URL tương đối; subdirectory cần dấu `/` cuối, ví dụ `https://example.test/redmine-mcp-docs/`.

Không serve repository root. Credential, `.env`, snapshot, Git metadata và file private không liên quan bị loại. `.env.example` là template tracked, chỉ được copy khi linked. Review nội dung trước publication; helper không deploy ra ngoài.

## Bàn giao xác minh

[Checklist portal](/vi/guides/verification.md) gồm offline, copy/highlight/Mermaid, ngôn ngữ, deep link/heading/404, mobile/theme/resize, export refresh/removal, boundary và root/subdirectory hosting. Export/serve không tự chạy test, browser, Inspector hoặc live call. Chỉ thực hiện khi assignment riêng cho phép, ghi rõ kết quả và giới hạn. Nghiệm thu MCP vẫn theo roadmap/coverage canonical.
