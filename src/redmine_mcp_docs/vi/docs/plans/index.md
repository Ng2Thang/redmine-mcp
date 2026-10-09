# Lộ trình chức năng và trạng thái task

> Bản tiếng Việt được biên tập từ [tài liệu tiếng Anh gốc](#/docs/plans/index.md). Bản gốc là nguồn chuẩn cho hợp đồng và hồ sơ đầy đủ. Tên API, lệnh, ngày, waiver và giới hạn nghiệm thu được giữ nguyên; việc dịch không thực hiện kiểm thử.

Đây là bản tổng hợp tiếng Việt của dashboard kế hoạch. Tài liệu task liên kết vẫn dùng tiếng Anh nếu chưa có bản dịch; thông báo ngôn ngữ sẽ xuất hiện. Không xem trạng thái của một task phụ thuộc hoặc giai đoạn lịch sử là nghiệm thu tự động cho mọi công cụ.

## Trạng thái hiện tại :id=current-status-2026-10-09

Danh mục đăng ký gồm **18 đọc/18 ghi**. Reader mặc định read-only; writer yêu cầu deployment riêng, gate và quyền người gọi.

| Công việc | Trạng thái và phạm vi |
| --- | --- |
| PREP-020 | Đã đối soát danh mục lịch sử 17 đọc/15 ghi; 1.086 offline/21 owned live ngày 2026-10-07; còn khoảng trống rộng hơn |
| PREP-021 | Tài liệu được cập nhật theo evidence; không chạy xác minh |
| PREP-022–026 | Functional acceptance pass: 1.395 offline, 23 owned live và Inspector |
| PREP-027 | GET retry được nghiệm thu theo evidence riêng; mutation vẫn một lần |
| TOOL-032/033 | Version creation và membership batch có native acceptance trong PREP-020 |
| TOOL-034/035 | Reporting estimate/time log có focused acceptance; giữ giới hạn visibility và scope |
| TOOL-036 | Tag filtering được kiểm tra trên Redmine 6.0.5 do người dùng chọn; full 7.0.2, overlap hai tag và private-role acceptance còn pending |
| TOOL-037 | Tag assignment đã bị loại khỏi phạm vi theo yêu cầu; mã retire, không tái sử dụng |
| TOOL-040 | Project time-entry activities đã triển khai; kiểm thử được miễn theo yêu cầu người dùng |
| TOOL-041 | Create time entry đã triển khai; kiểm thử pending |
| TOOL-042 | Update time entry có evidence 61 unit/99 integration/10 native; chưa có final clean full rerun |
| TOOL-043 | Delete time entry có 32 unit/82 integration/1.889 full offline và 12 native qua hai lần chạy |
| PREP-028, BUG-001 và release readiness | Công việc/giới hạn chưa đóng; không tuyên bố production readiness |

## Time entry

Kế hoạch ngày 2026-10-08 nêu các time entry 919–924 trên issue 491–496 theo thông tin người dùng. Đây không phải kết quả xác minh hoặc sự cho phép sửa các entry đó. Update/delete được thiết kế độc lập, dùng linkage issue/project và credited user chính xác; không phụ thuộc nghiệm thu create.

TOOL-041 tạo một time entry cho người gọi đã xác thực trên một issue nhìn thấy, yêu cầu ngày rõ ràng và số giờ dương; activity mặc định chỉ dùng theo native contract. Không ghi cho user khác, không tạo project-only log và không cung cấp bulk/admin activity tools. `allowed_all` không tự tạo một operation chưa được triển khai.

## Các giai đoạn lịch sử

Reader roadmap ban đầu gồm TOOL-001–012 và PREP-001–004. Các bước triển khai/static handoff không thay thế runtime acceptance. PREP-005 pin runtime được miễn giai đoạn kiểm thử; TOOL-014 có static handoff; các bước TOOL-015–019 từng blocked hoặc waived theo từng task. Download attachment được retire và route content bị từ chối.

PREP-007/008 chuẩn bị writer và fixture; TOOL-020–030 ghi nhận coding, static checks và các bước nghiệm thu riêng. Những trạng thái pending lịch sử phải được đọc cùng evidence mới hơn, không viết lại như thể evidence đã có tại thời điểm đó.

Multi-user writer ngày 2026-10-05 triển khai permission matrix, personal-key admission và discovery theo người gọi qua PREP-010–014. Scope gồm schema superset chung rồi resource capability discovery, luôn giữ deployment ceiling và reader isolation. Các task ban đầu bị chặn bởi verification; người dùng đã chỉ rõ coding không tự chạy kiểm thử. TOOL-031 báo capability theo project, với known/partial/unknown evidence.

PREP-015 bổ sung concurrency mặc định 50, admission wait 30 s, 30 upstream attempt và deadline read 90 s. Static checks ở handoff lịch sử không chứng nhận live behavior. PREP-016/017/018 sau đó hoàn tất 102 unit, 395 integration, 14 owned live và supplement Inspector/Edge trên cổng 3001 riêng; môi trường 6.0.5 chung được giữ nguyên.

TOOL-032 tạo Target version; TOOL-033 là một task kết hợp listing và batch membership writes. Native criteria được nghiệm thu trong PREP-020 ngày 2026-10-07. Không tách các task bổ sung hoặc đóng mọi gap bằng một kết quả chung.

## Cách đọc trạng thái

| Trạng thái | Ý nghĩa |
| --- | --- |
| discovery | Đang tìm hiểu nhu cầu và evidence |
| specified | Outcome và contract đã được mô tả |
| planned | Task đã qua quyết định kế hoạch; dependency có thể chưa hoàn tất |
| implementing | Đang triển khai |
| verifying | Đang thực hiện nghiệm thu được cho phép |
| complete | Triển khai và tiêu chí nghiệm thu của phạm vi đó đã đạt |
| blocked | Thiếu quyết định, dependency hoặc evidence cần thiết |

Đọc dependency, next action và evidence mới nhất của task trước khi thực thi. Những đề xuất chưa được giao như issue deletion, admin/Gantt/wiki/search không phải capability đang có và không tự khôi phục REST backlog. Release PREP-009 vẫn phải đạt tiêu chí release riêng.

Xem [quy trình task](/vi/docs/workflows/redmine-tools.md), [ma trận kiểm thử](/vi/docs/plans/testing-coverage.md) và [ledger](/vi/docs/testing/evidence/current-catalog-acceptance.md). Dashboard tiếng Anh chứa đầy đủ bảng commit, task và liên kết lịch sử.
