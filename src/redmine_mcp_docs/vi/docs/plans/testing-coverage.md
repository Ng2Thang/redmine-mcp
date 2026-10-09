# Ma trận phạm vi kiểm thử

> Bản tiếng Việt được biên tập từ [tài liệu tiếng Anh gốc](#/docs/plans/testing-coverage.md). Bản gốc là nguồn chuẩn cho hợp đồng và hồ sơ đầy đủ. Tên API, lệnh, ngày, waiver và giới hạn nghiệm thu được giữ nguyên; việc dịch không thực hiện kiểm thử.

Trang này tổ chức lại phạm vi và kết quả lịch sử của ma trận chuẩn. Số lượng thuộc từng revision, không cộng thành coverage hiện tại hoặc suy rộng sang mọi tổ hợp quyền. Các mã scenario được giữ nguyên để tra cứu task và bằng chứng tiếng Anh.

## Phân lớp và scenario

| Mã | Phạm vi |
| --- | --- |
| UNIT-001 | Validation/service/auth nghiêm ngặt của baseline |
| UNIT-002 | Settings/import offline, read policy, capability/role và budget |
| UNIT-003 | Input writer, deny policy và port của 11 writer ở giai đoạn baseline |
| INT-001 | SDK reader và REST, gồm 15 reader ở giai đoạn mở rộng |
| INT-002 | Writer: đúng method/path, một lần dispatch, verification và gate |
| INT-003 | Error/uncertainty, không retry mutation, GET kiểm chứng thất bại |
| INT-004 | Bounded read, preview và yêu cầu thu hẹp scope; proxy/link/deadline |
| INT-005 | Session, rotation, POST/GET/DELETE, lifespan, concurrency, readiness và cleanup |
| LIVE-001 | Gọi công cụ, đối chiếu state native và cleanup thuộc sở hữu |
| LIVE-002 | Role, private resource, author/tracker, closed/archived/module |
| LIVE-003 | Reader deny, admin không bypass gate; supplement Inspector/Edge |
| LIVE-004 | Permission kế thừa/role theo group và revocation |
| LIVE-005 | Commit native rồi lỗi/timeout được inject, single attempt và reconciliation |
| GATE-001 | E2E opt-in; thiếu flag bị từ chối trước fixture |

Tên scenario mô tả kế hoạch, không chứng minh mọi nhánh đã pass. Baseline lịch sử có 26 operation, 15 đọc/11 ghi; download attachment đã retire và pagination gate đã thay đổi. Bộ 356 case dạng phẳng được chuyển vào unit/integration và helper chung. PREP-004 giữ nguyên bằng chứng có ngày của nó.

## Kết quả theo giai đoạn

| Ngày/giai đoạn | Bằng chứng | Giới hạn |
| --- | --- | --- |
| PREP-016/017/018, 2026-10-06 | 102 unit + 395 integration = 497 offline; 14 live; Inspector/Edge supplement, cleanup và static checks pass | Môi trường riêng cổng 3001; không suy rộng sang production |
| TOOL-032 | 80 case feature + 4 matrix, 581 offline ở giai đoạn triển khai | Native acceptance ban đầu pending, sau pass trong PREP-020 |
| TOOL-033 | 155 case riêng: 86 unit/69 integration; 736 full offline | Native acceptance ban đầu pending, sau pass trong PREP-020 |
| TOOL-034/035, 2026-10-06 | 883 offline, gồm 139 reporting và 8 shared reader-error case; 2 focused owned live, 6 Inspector calls | Fixture reporting riêng; không cấp quyền đọc issue bằng quyền xem project-only time log |
| PREP-020, 2026-10-07 | 1.086 offline trong 335,59 s; 21 live trong 115,61 s; 49 allowed_all case; Inspector pass | Danh mục 17 đọc/15 ghi, H1–H6 chưa được đóng toàn bộ |
| PREP-022–026, 2026-10-07 | 1.395 offline trong 724,39 s; 23 live trong 246,84 s; Inspector pass | CI, ngưỡng coverage, recovery và production readiness hoãn |
| TOOL-042 | 61 unit/99 integration/10 native; 1.755 full pass và 1 lỗi cũ, rerun sửa lỗi pass | Không có full run cuối sạch sau 7 case muộn |
| TOOL-043 | 32 unit/82 integration, 1.889 full offline pass, 12 native qua hai lần chạy | Fault/policy matrix có giới hạn; không có một lần cuối chạy cả 12 |

Reporting kiểm tra attribution, date range/order, project-only log và quyền own/all. Tám ngày × 12 giờ = 96 chỉ đúng khi scope trả đủ dữ liệu. Fixture được tạo riêng và cleanup; không thay dữ liệu project của người dùng.

PREP-020 kiểm tra version/membership native, fixture 4 project/5 role, revocation có scope được khôi phục và Inspector read compatibility. 256 file format và mypy trên 120 file là kết quả static lịch sử. Không sửa permission đang có ngoài phạm vi fixture sở hữu. PREP-022–026 phát hiện và sửa schema union/null, SDK cap và clear assignment; warning dependency được ghi nhận tại thời điểm đó.

## Bàn giao

TOOL-040 được người dùng miễn kiểm thử; TOOL-041 còn pending. Không chạy kiểm thử chỉ vì mở trang này. Chọn revision, scenario, fixture thuộc sở hữu và quyền thực thi trước khi dùng các lệnh trong [lộ trình kiểm thử](/vi/docs/testing-roadmap.md). Theo dõi chi tiết ở [ledger](/vi/docs/testing/evidence/current-catalog-acceptance.md) và các trang evidence.
