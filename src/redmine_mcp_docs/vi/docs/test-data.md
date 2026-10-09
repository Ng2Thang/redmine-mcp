# Dữ liệu kiểm thử tổng hợp

> Bản tiếng Việt được biên tập từ [tài liệu tiếng Anh gốc](#/docs/test-data.md). Bản gốc là nguồn chuẩn cho hợp đồng và hồ sơ đầy đủ. Tên API, lệnh, ngày, waiver và giới hạn nghiệm thu được giữ nguyên; việc dịch không thực hiện kiểm thử.

Helper seed chuẩn bị dữ liệu quản trị cho môi trường local có marker; đây không phải kiểm thử ứng dụng và không phải fixture nghiệm thu E2E riêng.

## Các chế độ

```bash
bash scripts/seed.sh base
bash scripts/seed.sh history
bash scripts/seed.sh all
bash scripts/seed-history.sh
```

Chạy từ repository root sau khi service sẵn sàng. `dev-up.sh` chỉ chuẩn bị baseline. `seed-history.sh` chuyển tiếp sang chế độ history. Chế độ `all` dừng nếu baseline chưa hoàn tất.

Ngày 2026-10-06, generator được hợp nhất vào `tools/seed/generate.py`; các module cũ `generator.py` và `history.py` được loại bỏ. Entry point và initializer không thực thi seed khi import. Rails bootstrap vẫn riêng biệt. Linux lock được import muộn để cho phép đọc/import source trên Windows. Luồng chính: đọc state → tạo baseline → đối soát project → tạo history với prerequisite, lock và checkpoint → ghi manifest atomic.

Việc refactor ngày đó không chạy kiểm thử seed. Dataset parity và resume vẫn cần assignment xác minh riêng.

## Baseline

Marker là `redmine-mcp-synthetic-v1`; generator từ chối môi trường không rỗng chưa xác định. Rails tạo role, user và custom field; Python REST tạo 4 private project, membership, 150 issue, comment, transition, relation và 2 attachment. Chỉ ghi completion sau khi mọi bước thành công.

150 issue gồm 110 issue chính, 20 issue con và 20 issue hạn chế. Reader có quyền xem 128 issue baseline với bộ lọc status phù hợp; đây là thiết kế dataset, không phải tuyên bố kiểm thử permission tự động. Reader không được thấy private note hoặc membership bị hạn chế.

Baseline hoàn tất được bỏ qua. Baseline bị ngắt không tự resume; chỉ reset khi môi trường thuộc sở hữu và có thể bỏ đi. Không sửa manifest thủ công.

## History

History thêm 2 project cha và 6 project con, 20 user, 12 sprint version, 300 issue và 900 time entry. Mỗi project cha có 6 sprint, khoảng 15 ngày và cấu hình sharing theo dataset. Reader thấy 7 project; `History Beta Private` vẫn riêng tư.

Ngày anchor là ngày UTC khi bắt đầu; dữ liệu trải về 90 ngày trước đó, còn timestamp tạo tài nguyên là thời điểm chạy thật. Manifest lưu ngày, ID và tiến độ để resume. History hoàn tất được bỏ qua; reset xóa checkpoint và backup bao gồm state.

| Dataset | Số lượng |
| --- | --- |
| Tổng project sau base + history | 12 |
| Tổng issue | 450 |
| Time entry | 900 |
| Issue reader nhìn thấy trước thao tác thủ công | 128 baseline + 263 history = 391 |
| Issue history hạn chế | 37 |

Các số này không bao gồm tài nguyên không liên quan hoặc fixture E2E riêng.

## Manifest và dữ liệu riêng tư

`env.json`, `credentials.json`, `manifest.json`, history manifest và backup nằm trong `.local/`. Dùng khóa ngữ nghĩa như `projects.alpha-api`, `versions.alpha:01`, `issues.001`, `time_entries.001-1` để lấy ID hiện tại. ID có thể thay đổi sau reset. Không commit hoặc công khai credential, attachment và database dump.
