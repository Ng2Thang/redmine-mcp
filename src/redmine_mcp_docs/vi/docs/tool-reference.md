# Danh mục công cụ :id=tool-reference

> Bản tiếng Việt được biên tập từ [tài liệu tiếng Anh gốc](#/docs/tool-reference.md). Bản gốc là nguồn chuẩn cho hợp đồng và hồ sơ đầy đủ. Tên API, lệnh, ngày, waiver và giới hạn nghiệm thu được giữ nguyên; việc dịch không thực hiện kiểm thử.

## Danh mục và phạm vi hỗ trợ :id=catalog-and-support-scope

Danh mục hiện tại có **18 thao tác đọc và 18 thao tác ghi**. Reader mặc định chỉ công bố thao tác
đọc; writer riêng công bố thêm các thao tác ghi được cấu hình. Discovery personal-key phụ thuộc
người gọi; `conditional`/`unknown` không phải quyền được cấp. Xem [cấu hình](configuration.md#separate-writer-deployment)
về xác thực, operation list và `allowed_all`. Schema chuẩn nằm ở feature route/model và OpenAPI/MCP.

[Bằng chứng ngày 2026-10-07](testing/evidence/current-catalog-acceptance.md) chỉ bao gồm danh mục
17 đọc/15 ghi trước đó: **1,086** case offline và **21** case trên Redmine 7.0.2 riêng đã pass.
Revision, kịch bản và giới hạn H1..H6 xác định phạm vi. Không xác nhận mọi phiên bản hay production.
Tải nội dung attachment trực tiếp đã ngừng; reader trả metadata/link.
`list_project_time_entry_activities` đã triển khai nhưng người dùng miễn kiểm thử, chưa xác nhận runtime.
`create_time_entry` đã triển khai và còn chờ kiểm thử. `update_time_entry` và `delete_time_entry`
có [bằng chứng riêng](testing/evidence/tool-042-testing.md), [tương ứng](testing/evidence/tool-043-testing.md).
Các thao tác mới không thuộc ledger cũ.

## Kiểm tra input MCP :id=mcp-input-validation

Schema input MCP được khôi phục từ OpenAPI REST trước discovery và cache SDK. Union/nullable giữ
mọi nhánh, default và giới hạn: `update_issue.assigned_to_id` nhận số nguyên dương, `"me"` hoặc
`null` để bỏ assignment. Các trường version nullable và `list_time_entries.user_id` cũng giữ
hợp đồng route. Validator model REST vẫn kiểm tra quy tắc OpenAPI không biểu diễn đủ; subject
issue được gửi dưới dạng null vẫn lỗi. Chính sách unknown property không đổi.
PREP-022 có bằng chứng SDK/Inspector/native trong [regression preparation](testing/evidence/prep-022-026-testing.md).

## Kiểm tra trường response :id=declared-response-field-validation

ID tài nguyên/tham chiếu, kể cả parent/custom-field và receipt, phải là JSON integer dương.
Không nhận bool, string, float, zero hoặc âm. Filesize, download count, count/offset là integer
không âm; limit dương; flag chỉ nhận JSON boolean. `Issue.done_ratio` là integer 0..100, mặc
định zero khi thiếu. `Project.status` nhận mọi integer dương, không thêm enum đóng.
Relation delay là integer có dấu hoặc null. Date parsing, giờ hữu hạn không âm, optional field,
observations và collection rỗng giữ hành vi cũ; parent issue vẫn là dictionary với `id` được kiểm tra.

Upstream read sai trường khai báo trả `502 upstream_response` an toàn hoặc MCP tool error.
Preflight sai dữ liệu không gửi mutation. Read-back sai sau ghi giữ receipt accepted/uncertain,
verification unavailable và safe error nếu result hỗ trợ. Không suy ra ID hoặc tự retry creation.
PREP-025 có [bằng chứng riêng](testing/evidence/prep-022-026-testing.md); không thêm operation/field/call mới.

## Quản lý membership project :id=project-membership-management

| Công cụ | REST endpoint | Input |
| --- | --- | --- |
| `list_project_members` | `GET /api/v1/projects/memberships` | `project_ids` duy nhất, 1..10 ID dương; `limit=25` (1..100), `offset=0` |
| `add_project_members` | `POST /api/v1/projects/memberships/batch` | 1..10 `items` có `project_id`, `user_id`, `role_ids` |
| `update_project_members` | `PUT /api/v1/projects/memberships/batch` | 1..10 `items` có `project_id`, `membership_id`, `role_ids` |
| `delete_project_members` | `DELETE /api/v1/projects/memberships/batch` | JSON body 1..10 `items` có `project_id`, `membership_id` |

Listing dùng reader. Mutation cần writer bật riêng, operation allowlist và `manage_members` tại
project. Gate pinned/personal-key áp dụng cả admin. ID phải integer dương; không nhận bool/null,
unknown field, project/target trùng, role list rỗng/trùng. Add duy nhất theo project/user;
update/delete theo membership ID. Ghi chỉ hỗ trợ user, không hỗ trợ group giả làm user ID.

MCP list: `{"project_ids":[5,9],"limit":25,"offset":0}`. REST lặp query `project_ids=5&project_ids=9`.
Result `results` theo thứ tự input; mỗi project có `project_id`, outcome `read`/`rejected`/`not_executed`,
`page` và `error` nullable. Page có `items`, `total`, `limit`, `offset`, `visibility`, `pagination_policy`.
Membership có `id`, `project:{id,name}`, đúng một `user` hoặc `group`, cùng `roles:{id,name,inherited}`.
Flag inheritance thiếu thành false. Role ID lặp từ nhiều nguồn được gộp theo lần gặp đầu,
inherited=true nếu có bất kỳ nguồn kế thừa; tên cùng ID xung đột vẫn lỗi. Requested role ID phải duy nhất.
Collection thiếu/sai không được biến thành inventory rỗng. Offset áp dụng riêng từng project;
`scope_required` của một project không bỏ qua project khác, nhưng lỗi credential/transport/budget
chung có thể dừng phần còn lại. Redmine 7.0.2 công bố `view_members` public; quyền project/state vẫn áp dụng.

Preflight toàn batch kiểm tra project, quyền cần thiết, user, project của membership, role ID,
không có membership trùng khi add và điều kiện inheritance khi delete. Add đọc memberships của
user; chỉ fallback inventory project đầy đủ, có giới hạn khi expansion bị bỏ qua.
`membership_already_exists` trả trạng thái quan sát được, không đổi add thành update.
Một lỗi preflight đã biết hoặc hết budget ngăn mọi mutation. Scope batch mặc định:
**300 physical requests**, **30 MiB GET bytes**, deadline phối hợp **300 giây**, độc lập budget reader.
PREP-023 ghi nhận fixture manager 10 items; inventory lớn/latency/cap tùy chỉnh vẫn có thể cần batch nhỏ hơn.
Proof project/user chỉ tái sử dụng trong preflight; execution lấy bằng chứng mới trước từng ghi.
Mutation đang chạy có timeout riêng và có thể xong sau deadline batch; cancellation truyền tiếp.

Sau preflight, ghi tuần tự, một POST/PUT/DELETE native cho mỗi item thử. Native rejection riêng
có thể tồn tại cùng item accepted. Lỗi credential/transport/budget chung và uncertain write dừng
item sau. Không retry/rollback/transaction xuyên project. Chờ admission tính vào deadline;
sau khi lấy capacity phải kiểm tra lại deadline, release permit nếu hết hạn, giữ receipt trước đó.

Write result có `phase=preflight_failed|executed` và `results` theo thứ tự. Mỗi item có `index`
từ zero, project/target ID nullable, `outcome=accepted|rejected|uncertain|not_executed`,
`verification=matched|mismatch|unavailable`, `requested_role_ids`, `observed_membership`,
`observed_present`, `permission_state=conditional|unknown|denied`, `error:{code,message,status}`.
Batch envelope HTTP 200 có thể chứa item rejected; lỗi input/auth/gate toàn cục vẫn dùng HTTP error.
Accepted chỉ ghi nhận native success. Verification so role hiệu lực với requested set; Redmine
có thể giữ role kế thừa/không quản lý được và lọc role assignable, nên accepted vẫn có mismatch.
API role không công bố đầy đủ managed-role configuration; thiếu bằng chứng không đồng nghĩa denied.

Delete chặn group và bất kỳ role kế thừa trước dispatch; native còn đòi mọi role target manageable.
Matched delete cần absence trong inventory project đầy đủ, đọc được; 404 membership, thiếu page hoặc
mất project access không đủ. Read-back lỗi không xóa acceptance. Thay membership có thể truyền xuống
project con hoặc xóa default assignee project/category; xác minh tác động này cần assignment riêng.
Đối chiếu project/user khi add, membership ID/role khi update/delete trước retry kết quả uncertain.
Disconnect/shutdown có thể làm mất receipt; thiếu response không chứng minh thất bại.
PREP-020 có [bằng chứng Redmine 7.0.2 riêng](testing/evidence/current-catalog-acceptance.md);
container dùng chung 6.0.5 không phải bằng chứng target version.

## Tạo project version :id=create-project-version

`create_project_version`: writer-only, `POST /api/v1/projects/{project_id}/versions`, cần gate
operation và `manage_versions` project. Lấy project ID qua `list_projects`.
`name` 1..60 ký tự, không chỉ whitespace; `description` tối đa 255; `due_date` là `YYYY-MM-DD` hợp lệ.
Giữ cách viết/whitespace name; description rỗng được phép. Optional bỏ qua/null không gửi upstream.
Date rỗng/datetime và unknown body field bị chặn. Cố định `status=open`, `sharing=none`;
không update version/chọn sharing/custom field/wiki/assign issue.

Receipt có `outcome=accepted|existing|uncertain`, `upstream_accepted`, `resource_id`,
`verification`, `observed_version` gồm sharing và `error`. REST HTTP 200 không chứng minh tạo/verify thành công.
Hints: read-only false, destructive false, idempotent false, open-world true.
Native 201 lấy ID rồi GET độc lập so project/name/status/sharing/optional field đã gửi.
Read-back cần `view_issues`, nhưng đây không phải điều kiện thêm cho creation; lỗi GET giữ acceptance.

Sau native 422, lookup có giới hạn có thể trả đúng một version cùng name phân biệt hoa/thường và
thuộc project yêu cầu; loại version share từ project khác. Receipt `existing`, upstream false,
verification unavailable và lỗi `version_already_exists`: native từ chối tạo, metadata hiện có
không được thay bằng input. Client phải hiển thị lỗi dù có resource data. Match không đọc được,
sai/không có/mơ hồ giữ validation error gốc. Chỉ gửi một write; dispatched timeout, status success
không mong đợi hoặc body/ID không dùng được tạo uncertainty; đã thấy 201 vẫn giữ upstream true.
Đối chiếu `list_project_versions` trước retry; cùng name sau timeout không chứng minh lần gọi tạo nó.
PREP-020 có acceptance tool-032 về optional/duplicate/creation không có issue-read permission.

## Capability project của người gọi :id=caller-project-capabilities

`list_my_project_capabilities`: `GET /api/v1/users/current/project-capabilities`, `limit=25`
(1..100), `offset>=0`, `include_reasons=false`. Không nhận account/key arguments.
`project_id` chọn một project nhìn thấy, kể cả ngoài page; `operation_id` lọc công cụ theo project.
Mặc định chỉ giữ match `conditional`; `include_unknown=true` thêm unknown trong request lọc operation.
Ví dụ `{"project_id":3,"operation_id":"create_issue"}`. Filter trước pagination; `total` là
project match; scoped request trả `global_tools=[]`. Không nhận global operation như upload,
operation không biết; ghi bị deployment/account chặn không có match. Inventory operation filter
tối đa **10,000** visible projects trong deadline; vượt giới hạn yêu cầu `project_id`.

Response có `user_id`, `items`, `total`, `limit`, `offset`, `visibility`, `global_tools`.
Project có `id`, `name`, `roles`, `permissions`, `permissions_state`, `membership_state`, `tools`.
Role unique/sort ID, name nullable; vừa trực tiếp vừa inherited thì inherited=false (khác cách
gộp của membership list). Permission là hợp unique/sort của mọi role đọc được, không xếp hạng theo
ID/name. `known`: mọi role đọc được; `partial`: một phần; `unknown`: không đọc được hoặc thiếu
membership. Partial giữ union biết; unknown permission=null; known [] là thật sự không có quyền
trong role báo cáo. Public project thiếu membership rõ ràng vẫn unknown.
Tool mặc định chỉ có `operation_id`, `state`; `reason` bị bỏ hẳn trừ khi include_reasons=true.
Ghi disabled/account restricted/denied bị loại; conditional có bằng chứng cần thiết, unknown thiếu bằng chứng.

| Reader | Bằng chứng cho conditional | Kiểm tra vẫn còn khi gọi |
| --- | --- | --- |
| `get_project` | Có trong visible-project page | Access và metadata hiện tại |
| `get_issue`, `list_issues`, `list_project_versions` | `view_issues` | Visibility, module, private/shared state |
| `list_project_issue_categories` | `view_issues` hoặc `manage_categories` | Module và project access |
| `list_project_files` | `view_files` | Files module và visibility |
| `list_project_time_entry_activities`, `list_time_entries` | `view_time_entries` | Module, access, visibility; không cấp log_time |
| `list_issue_time_entries` | `view_issues` và `view_time_entries` | Issue preflight, module, role visibility |
| `get_attachment` | Một trong các quyền xem issue/file/document/news/message/wiki | Container thật, chỉ metadata/link |

Administrator được Redmine báo rõ cho bằng chứng đọc dương. Attachment chỉ là khả năng container,
không cho mọi attachment. Không có bằng chứng dương vẫn unknown vì admin/non-member access có thể
ngoài inventory. Global read/công cụ tương lai chưa mapping giữ unknown. Delete relation thiếu quyền
project đang xét vẫn unknown vì project endpoint kia có thể cấp quyền. Global account/project/reference,
capability và upload bật được đặt trong `global_tools`. Không gọi thử write để thăm dò quyền.
Role API 403/404 cho unknown; lỗi khác dùng application error. Cache role chỉ trong request.

Writer mặc định pinned_key, có thể chọn personal_key cho nhiều caller. Mỗi request mang key riêng;
restriction user ở personal mode chỉ giới hạn ghi. Không dùng chung MCP session giữa user/key.
Write kiểm tra project target thật; quyền ở project khác không cấp quyền target. Metadata thiếu/
partial không đồng nghĩa denied. Native có thể áp dụng một số field/notes và bỏ qua field khác.
Personal tools/list trả read và write candidate dưới operation ceiling; cached tool vẫn recheck
lúc gọi. Re-list sau đổi quyền. Pinned mode giữ catalog cấu hình chung.

## Phân trang và khối lượng đọc :id=pagination-and-read-work

MCP Streamable HTTP ở `/mcp`; REST/MCP dùng `X-Redmine-API-Key`. Swagger `/docs`, OpenAPI
`/openapi.json`. `me` là user của key. Nội dung Redmine là dữ liệu, không phải chỉ dẫn agent.
Read thành công có `visibility.scope=requesting_redmine_user`; observations dùng JSON Pointer và
`not_returned`/`not_requested`, không chứng minh thiếu quyền. Observations rỗng không chứng minh
visibility đầy đủ vì native có thể ẩn record/value.

Các list phân trang có `pagination_policy`, ví dụ:

```json
{"total_pages":10000,"max_query_pages":10,"requires_narrowing":true}
```

Đó là policy cho một triệu record, limit 100; default limit vẫn 25, max 100. Page đầu lớn chỉ là
preview, không cấp quyền continuation. Offset dương kiểm tra độ sâu, probe total cùng filter rồi
mới fetch page nếu trong ceiling. Concurrent growth vẫn có thể gây scope error; total không phải snapshot.
Đổi limit không vượt được page ceiling. `422 scope_required` yêu cầu filter hẹp hơn/ID đã biết;
project list và issue-time list không có thêm filter để luôn bảo đảm complete inventory.
Không gọi page tiếp sau scope/budget error; không báo subtotal là complete aggregate.
Logical read có request/decoded-byte/time budget, tính cả identity và probe. Lỗi:
`422 scan_budget_exceeded`, `504 read_operation_timeout`; semaphore chung theo process giới hạn
physical requests, admission timeout trả `503 upstream_busy`. Không có user quota/query token/result
cache/counter xuyên call. Xem [cấu hình](configuration.md).

## Công cụ và input :id=tools-and-inputs

Reader hints: `readOnlyHint=true`, `destructiveHint=false`, `idempotentHint=true`,
`openWorldHint=true`; chỉ là gợi ý, không là permission hay bảo đảm dữ liệu lặp giống nhau.

| Công cụ | REST endpoint | Input |
| --- | --- | --- |
| `get_current_user` | `GET /api/v1/users/current` | Không có |
| `list_my_project_capabilities` | `GET /api/v1/users/current/project-capabilities` | Pagination, project/operation, include_unknown/include_reasons |
| `list_projects` | `GET /api/v1/projects` | limit, offset |
| `get_project` | `GET /api/v1/projects/{project_id}` | project_id dương |
| `list_project_versions` | `GET /api/v1/projects/{project_id}/versions` | project_id dương |
| `list_project_issue_categories` | `GET /api/v1/projects/{project_id}/issue-categories` | project_id dương |
| `list_project_files` | `GET /api/v1/projects/{project_id}/files` | project_id dương |
| `list_project_time_entry_activities` | `GET /api/v1/projects/{project_id}/time-entry-activities` | project_id, không pagination |
| `list_project_members` | `GET /api/v1/projects/memberships` | project_ids, limit, offset |
| `list_issues` | `GET /api/v1/issues` | Các filter ở bảng dưới, include, tags_any, pagination |
| `get_issue` | `GET /api/v1/issues/{issue_id}` | issue_id, include CSV |
| `get_attachment` | `GET /api/v1/attachments/{attachment_id}` | attachment_id dương |
| `list_issue_time_entries` | `GET /api/v1/issues/{issue_id}/time-entries` | issue_id, limit, offset |
| `list_time_entries` | `GET /api/v1/time-entries` | project_id, user_id dương/"me", issue_id, spent_from/to, include_subprojects=false, pagination |
| `list_issue_statuses` | `GET /api/v1/issue-statuses` | Không có |
| `list_trackers` | `GET /api/v1/trackers` | Không có |
| `list_issue_priorities` | `GET /api/v1/issue-priorities` | Không có |
| `list_document_categories` | `GET /api/v1/document-categories` | Không có |

| Tham số list issue | Mặc định và giá trị |
| --- | --- |
| limit / offset | 25, 1..100 / 0, không âm |
| project_id / category_id | Optional integer dương; category cần project |
| fixed_version_id | Optional Target version ID dương |
| include_subprojects | true; false cần project_id |
| status_id | "open", "closed", "*" hoặc chuỗi ID dương |
| assigned_to_id | "me" hoặc chuỗi ID dương |
| tracker_id / parent_id | Integer dương optional |
| updated_since | RFC 3339 có timezone, inclusive; normalize UTC giữ cùng thời điểm |
| sort | "id:asc" mặc định, "id:desc", "updated_on:asc", "updated_on:desc" |

Filter kết hợp AND; category/version lấy từ công cụ tham chiếu project. `status_id="*"` gồm closed.
Page có `items,total,limit,offset,visibility,pagination_policy`. Trước từng continuation kiểm tra
policy; tăng offset theo limit, dừng trên scope/budget error. Page rỗng sớm/continuation bị chặn
vẫn incomplete. Count native phải integer không âm, item count không vượt limit; limit/offset echo
nếu có phải đúng request. Issue/project có thể thiếu echo, time entry bắt buộc. Detail ID phải đúng target.

## Response :id=responses

`get_current_user` nhận `{}`, trả `id,login,firstname,lastname,mail,memberships,visibility`.
Email thiếu thành null với `/mail not_returned`; explicit null không thêm observation. Membership
có project/role, inherited thiếu thành false. Không trả key/account metadata khác. Memberships=[] hợp lệ,
thiếu/sai collection trả 502; ID user phải khớp principal. Authentication identity lookup và profile GET
là hai call riêng cùng key; không có pagination/expansion argument. Membership không phải toàn bộ
accessible project/effective permission inventory.

Project list trả identity/description/status/parent; detail thêm `is_public,created_on,updated_on`
nullable. List version/category/status/tracker/priority dùng envelope `items,visibility`, không còn
top-level array. Version có project/status/description/due_date và có thể share từ project khác.
Version/category yêu cầu total_count bằng array length; thiếu count/partial collection lỗi 502 vì
không có pagination được xác nhận. Order giữ native; category có assignee optional.

### Activity ghi thời gian của project :id=project-time-entry-activities

`list_project_time_entry_activities` dùng project detail `include=time_entry_activities`, cần
`view_time_entries` cho expansion. Trả activity ID/name active và override project thật, không đổi
sang global parent ID. Không pagination/count/sort guarantee. Expansion rỗng có mặt: items=[] không
observation. Expansion thiếu: items=[] kèm `/items not_returned`, nghĩa unavailable, không chứng minh
không activity. Null/nonarray, ID trùng/sai, name sai, project sai đều 502. Không chỉ default của caller
hay cấp log_time; get_project không đổi. Testing đã được miễn.

### Tạo time entry :id=create-a-time-entry

`create_time_entry`, writer-only `POST /api/v1/issues/{issue_id}/time-entries`, ghi một entry cho
caller. Cần issue ID dương, hours JSON number hữu hạn >0, spent_on `YYYY-MM-DD` rõ ràng; client
giải nghĩa "hôm nay" theo timezone user trước call. Không nhận bool/string hour/zero/âm/null/date sai.
Optional activity_id dương, comments string tối đa 1024, giữ cả rỗng. Không other-user/project-only,
custom field/batch/unknown field. REST issue ID ở path. Operation gate phải allow hoặc allowed_all.
Cần issue visibility và native `log_time`; view_time_entries chỉ cho discovery/read-back, không thêm
điều kiện creation. Native khởi tạo resolved project trước khi chọn caller-role/project/global default
activity. Activity bỏ qua dùng native selection; không default/activity sai có thể native rejection.
Không bypass required comment/custom field, closed/future/daily-hour policy/hook/plugin.
Hai call 8 giờ nếu cùng success tạo hai entry tổng16; limit có thể chặn call thứ hai không undo call đầu.

Receipt HTTP200 có accepted/uncertain, upstream true chỉ sau native201, resource_id nullable,
verification/field_verification và observed_time_entry GET độc lập. So issue/project/caller,
hours/date/optional đã gửi; field thiếu unavailable. Hours so theo làm tròn phút native rồi API hai
chữ số thập phân, không sửa submitted hours. Body201 không phải independent verification.
Một POST; 5xx/dispatched timeout/body/identity creation sai có uncertainty; failed GET giữ acceptance.
Uncertain không đổi thành accepted chỉ vì observation match. Đối chiếu ID hoặc list_time_entries
lọc issue, user "me", date có giới hạn trước retry; date/hours trùng không đủ nhận dạng creation.
Không automatic retry/dedup/rollback/atomic multi-issue. Kiểm thử còn chờ.

### Cập nhật time entry :id=update-a-time-entry

`update_time_entry`: `PUT /api/v1/issues/{issue_id}/time-entries/{time_entry_id}`, hai ID dương,
ít nhất một hours/spent_on/activity_id/comments. Hours hữu hạn >0, date calendar, activity dương,
comments strict string <=1024; "" xóa comment nếu native cho phép. Field bỏ qua không gửi PUT;
null/empty update/unknown field lỗi. Không move entry, đổi credited user, custom field/bulk.
Preflight xác nhận đúng entry/issue/project. Cần view_time_entries và edit_time_entries hoặc
edit_own_time_entries của **credited user**, không phải submitting author; log_time không đủ.
Writer/caller/gate/issue visibility vẫn áp dụng. Receipt có ID bắt buộc, upstream true sau native204,
verification/field verification/observed entry. Independent GET so input đã gửi và identity preflight;
native rounding như creation. Failed read giữ accepted; matched observation không xóa uncertainty.
Một PUT, không retry/undo/lock/optimistic concurrency/atomic preflight-write; hook có thể lặp khi gọi lại,
race có thể ghi đè hoặc đổi linkage. TOOL-042 có [bằng chứng scoped](testing/evidence/tool-042-testing.md),
không exhaustive plugin/policy/race. Aggregate issue sum stored hours khác API display rounding.

### Xóa time entry :id=delete-a-time-entry

`delete_time_entry`: `DELETE /api/v1/issues/{issue_id}/time-entries/{time_entry_id}`, hai ID dương,
không body/confirmation/filter/bulk; extra MCP argument lỗi. Xóa vĩnh viễn, native destruction hooks
đổi spent-time total. Preflight cùng caller xác nhận ID/issue/project/credited user; linkage sai422,
missing/forbidden/malformed safe error và zero DELETE; project-only entry bị loại.
Permission như update, own theo credited user; log_time không đủ. Một DELETE không body;
native204 tạo receipt HTTP200 accepted/upstream true. ID target giữ nguyên. Ambiguous dispatch
uncertain/upstream null. GET độc lập đúng ID: `still_present`/true, caller404 `not_found`/false,
denied/failed/malformed `unavailable`/null. Observation không viết lại outcome; caller404 không
chứng minh physical absence hoặc uncertain DELETE committed. Đã absent preflight 404 không gửi DELETE,
không tạo idempotent success. Không retry/undo/rollback/lock/If-Match; mỗi pair cần call/receipt riêng.
TOOL-043 có32unit/82integration riêng/12owned native case pass; fault receipt và moved-entry race có
kiểm tra, plugin tùy ý/TCP-loss/live visibility-policy change chưa được xác minh. Ví dụ entry919/issue491
không cho phép xóa incident thật hoặc dùng entry #919–#924 làm fixture.

### Issue, giờ ước lượng và giờ đã dùng

Issue list/detail có category/fixed_version nullable, start_date/due_date ISO hoặc null,
estimated_hours/total_estimated_hours hữu hạn không âm nullable. Spent_hours là trực tiếp,
total_spent_hours gồm issue con, có thể chỉ gồm time entry caller được thấy. Null không phải zero.
Field hour/estimate thiếu có not_returned theo path; explicit null không thêm observation.
Journal thêm updated_on/updated_by khi native cung cấp; attachment có content_url nullable,
không tự tải nội dung URL. Để cộng estimate/spent time: thu đủ phạm vi được phép, dedup issue ID,
dùng decimal, chỉ cộng giá trị trực tiếp; không cộng descendant total trên parent/child chồng lặp.
Null hoặc incomplete page phải báo partial/unavailable, không total đầy đủ. Numeric zero là giá trị biết.
Schedule date issue không lọc ngày ghi time; ví dụ September2026 giữ cả start/due trong
2026-09-01..2026-09-30 inclusive sau khi thu đủ scope. Kiểm tra detail cùng caller khi list estimate thiếu.

### Time log tổng quát :id=general-spent-time-logs

`list_time_entries` không cần issue. Bỏ project đọc mọi visible project; project mặc định không
subproject, true cần project và filter native rõ ràng không phụ thuộc default server. Issue filter
chỉ entry trực tiếp; không issue filter gồm project-only entry. Không thêm view_issues preflight.
User filter chọn credited user (có thể khác submitter/assignee). Spent_from/to ISO inclusive,
có thể độc lập; cả hai thì from<=to, lọc spent_on, không schedule/created time.
Entry có ID, project/user refs, issue_id nullable, hours hữu hạn không âm, spent_on,
activity/comments nullable. Issue ref thiếu không chứng minh unattached. Sort spent_on asc rồi native
entry ID tie-break. Required/present optional ref sai lỗi502. Total là entry count, không hours.
Thu đủ page được phép, dedup ID, decimal sum/group project/user/activity/date; null activity có nhóm
unavailable riêng. Không thêm issue spent_hours vì đếm đôi. Complete chỉ trong caller-visible scope,
có thể chỉ log của chính caller. Narrow filter thay phạm vi nếu không phải partition complete
không chồng lặp. Stop scope/budget; concurrent data không snapshot.

### Time entry của một issue :id=time-entries-for-one-issue

`list_issue_time_entries` trả entry trực tiếp của visible issue: id, issue_id, credited user,
hours, spent_on; không nhận dạng submitter. Cần issue visibility/time-entry permission. Không date/
assignee filter; large-issue complete breakdown có thể unavailable. Chọn issue khác đổi scope,
không hoàn tất issue cũ. Dedup/group user/decimal sum, stop policy/budget; empty không chứng minh
không có entry user khác. Schedule August không giới hạn dates entry trả về.

### Tags, expansion và catalog tham chiếu

`get_issue.tags`: string array assigned names khi được native trả, [] khi biết rỗng, null khi
unavailable; field thiếu `/tags not_returned`. Không cài endpoint/plugin/switch mới. Core7.0.2 +
Tags2.2.0 Light API đã xem không trả field; list/writer observation không có tags. Native issue_tags
filter vẫn hoạt động dù output không chứa assigned tag array. Không quản lý tag assignment/name qua MCP.
`list_issues.tags_any`: optional1..20 unique names, mỗi name1..255, ANY giữa tags AND với filter khác,
default open. Giữ case/comma/pipe; chặn null/[]/blank/duplicate/edge whitespace/control/%/_/backslash
vì native SQL LIKE. Case theo database; name hợp lệ không biết cho empty match. REST repeated tags_any.
Không env switch/probe/server modification. TOOL-036 focused offline/selected6.0.5 live/Inspector
pass, full7.0.2 và overlap/private-role acceptance còn chờ [bằng chứng](testing/evidence/tool-036-tag-filter-testing.md).

List include nhận attachments/relations CSV, bỏ qua thì arrays rỗng với not_requested; requested
missing not_returned. Detail include nhận children,attachments,relations,changesets,journals,watchers,
allowed_statuses theo caller order; mặc định journals+attachments, "" không request expansion.
Duplicate/unknown/empty segment lỗi422. Custom field id/name/value string/string array/null/multiple.
Children có nested issue/tracker/subject; relation có endpoints/type/delay; watcher ID/name;
allowed_status ID/name/is_closed; changeset giữ JSON object. Array rỗng unrequested không chứng minh absence.
Status catalog không xác định transition của issue; dùng allowed_statuses detail. Tracker catalog
không bảo đảm enabled project. Priority/document category trả id/name/is_default; document category
không cấp access document. Project files có metadata/content URL/digest/download count/version nullable,
không pagination/total/download; cần View files. Attachment metadata theo container access, optional
type/description/author observations; native404 có thể do stored file unreadable.

### Attachment và thao tác ghi issue

`download_attachment` không discovery, cached call lỗi; retired content REST403
`attachment_download_disabled` trước auth/upstream. Browser download dùng metadata link;
REDMINE_PUBLIC_URL map origin/subpath hợp lệ, không chứa key/token và cần Redmine browser auth.
Server không tạo file/export hay fetch content link.

`upload_attachment`: writer riêng, basename filename<=255 và strict content_base64; decoded cap
REDMINE_MAX_BINARY_BYTES mặc định5MiB. Native POST/uploads.json?filename=... raw octet-stream;
success có temporary unattached attachment_id/token. Receipt accepted/uncertain và independent
verification; failed GET không undo upload. Uncertain có thể đã tạo object tạm, đối chiếu trước retry.
Reader không discovery và REST403.
REST mutation body/MCP POST envelope có byte admission trước parse/auth, cả internal dispatch.
Cap REDMINE_MAX_REQUEST_BODY_BYTES optional, default
`max(REDMINE_MAX_RESPONSE_BYTES, 4 * ceil(REDMINE_MAX_BINARY_BYTES / 3) + 65536)` =10MiB.
Compact JSON maximum upload phù hợp cap; escaping/padding hoặc cap thấp có thể chặn file hợp lệ.
Encoded/decoded check độc lập. Lỗi413 request_body_too_large,400 invalid_request_body cho length
sai/xung đột,415 request_encoding_unsupported nếu encoding không identity; có X-Request-ID, zero upload.
Outer MCP HTTP error trước JSON-RPC nên không CallToolResult; internal REST dùng tool-error mapping.

`add_project_file`: project_id dương, token upload, basename filename, description/version_id optional;
version phải thuộc project. Native POST/projects/{id}/files.json204; receipt ID từ token, outcome,
upstream_accepted, verification GET project files và observed_file. Failed GET giữ accepted;
không tự retry token uncertain.
`update_attachment`: attachment_id, container_type project/version/issue, container_id và ít nhất
filename/description; filename<=255, empty description xóa, null/unknown lỗi, omitted không gửi PATCH.
Prove membership từ project files/version ref hoặc issue attachments, version owner qua metadata;
không thấy trong container declared trả safe404 trước mutation. Native PATCH/attachments/{id}.json;
receipt independent field verification/observed_attachment, không atomic membership+write.
`delete_attachment`: DELETE/api/v1/attachments/{id}, required query container_type/container_id,
unknown query lỗi, không body. Project/version cần manage_files; issue visibility và tracker-aware
edit_issues hoặc edit_own_issues author. Native 204 accepted; container GET absence matched,
present mismatch, failure unavailable/null. Visible absence không chứng minh bytes removed;
uncertain giữ nguyên; no retry/rollback. Hints destructive true/idempotent false.

`create_issue`: POST/api/v1/issues; project_id và subject nonblank<=255 trừ copy_from visible positive
source. Native copy có attachment/link effects, watchers theo destination permission, không subtree/
client clone. Cần add_issues destination, copy_issues source khi copy và field permission. Optional:
tracker/status/priority/category/fixed_version/assignee(ID hoặc me)/parent/description/start/due/
done_ratio/estimated_hours/is_private/custom_fields/uploads/watcher_user_ids. ID strict dương,
done_ratio0..100, hours hữu hạn>=0, calendar dates; reject duplicate IDs/inverted date range/unknown.
Omitted giữ default/copied value. Null clear description/assignee/category/version/parent/dates/hours;
field khác không nhận null. Custom field value string/string array/null. Upload token/filename thật,
description/content_type optional (native strip upload description); watcher unique user IDs.
Destination project ở query và payload, copy_from chỉ query. Native201 accepted, receipt ID,
verification/field verification/observed issue GET độc lập, không echo token. Native7.0.2 optional refs
omitted có thể biểu thị unset, hidden comparison unavailable, mismatch ưu tiên. Bad body/timeout có
thể không ID; không retry hoặc suy failure từ GET lỗi; native có thể bỏ field không editable.

`update_issue`: PUT/api/v1/issues/{id}, ít nhất field, custom/upload nonempty hoặc notes nonblank.
Field như create, có destination project_id, loại copy_from/watcher IDs; không delete attachment/
time entry/locking/conflict flag. Omitted không gửi, nullable clear như create. private_notes boolean
cần notes. Notes-only cần Add notes, không thêm Edit issues local. Native kiểm tra field/workflow/
parent/privacy/attachment/destination và có thể ignore field;204 chỉ acceptance. Receipt nullable
journal_id/observed issue/field verification; notes cần preflight journal IDs và journal mới do caller
viết. Note cũ giống không verify; ambiguous/hidden unavailable, observed difference mismatch.
Không atomic attribution dưới concurrency; uncertain có thể đã add note/upload.

`update_issue_note`: PUT/api/v1/issues/{id}/notes/{journal_id}, notes string (rỗng/whitespace được)
hoặc private_notes strict boolean, không null/unknown/empty update. Prove visible journal trong issue.
Cần Edit notes hoặc Edit own notes của author, Set notes private khi đổi privacy. Native
PUT/journals/{id}.json chỉ supplied journal fields, tự đặt updated_by, trả204. Receipt journal ID,
issue_id/outcome/upstream/verification/field_verification/observed_present/observed_journal.
GET cùng journal so supplied fields; hidden/omitted/absent/read lỗi unavailable. Clearing notes ghi đè,
7.0.2 vẫn giữ row nhưng visible history có thể mất; privacy cũng ẩn. observed_present=false không
chứng minh deletion/clearing. Không retry/atomic guarantee; destructive true, idempotent false.
Journal chứa id/user/notes/created_on/private_notes/details, detail property/name/old_value/new_value.

`create_issue_relation`: POST/api/v1/issues/{id}/relations, positive issue_to_id; relation_type default
relates, nhận duplicates/duplicated/blocks/blocked/precedes/follows/copied_to/copied_from.
Delay signed days chỉ precedes/follows. Chặn null/unknown/list/string/self/type-delay sai.
Cần Manage issue relations source và visibility cả hai; native cross-project/duplicate/cycle/ancestor
rules. Check cả issue trước một POST201. Receipt resource ID nullable; malformed201 giữ upstream
true nhưng uncertain nếu ID không đáng tin. GET relation exact ID so endpoints/type/delay;
missing/read lỗi unavailable, không suy existing pair là creation này. Normalize inverse type bằng
swap endpoints, relates sort ID, scheduling delay default0, loại khác null. Native journal cả hai,
scheduling có thể đổi downstream dates; verification relation không verify side effects.

`delete_issue_relation`: DELETE/api/v1/relations/{id}, gate operation; preflight relation visible và
ID trong cả hai endpoint contexts visible. Manage relation ở **một** endpoint project đủ, không
đòi cả hai/edit issues local. Empty204 accepted; resolved_relation và observations keyed endpoint IDs.
True nếu có, false nếu absent, null unavailable; một endpoint present => mismatch, cả hai absent
=> matched, còn lại unavailable. Native7.0.2 omits empty relations trên same-ID successful issue
được tính visible empty, nhưng failed/404 issue không chứng minh absence. Matched không chứng minh
stored-row deletion; native journal cả hai, không restore scheduling dates. No retry/rollback/atomic.

`add_issue_watcher`: POST/api/v1/issues/{id}/watchers, strict user_id dương; reject bool/null/string/
fraction/list/batch/unknown. Cần Add issue watchers và issue visibility, không thêm Edit issues/View
watchers local. User ID có thể User/Group principal. Một POST `{"watcher":{"user_id":2}}` sau
same-ID preflight. Native 204 có thể principal ineligible/no addition; receipt không invent resource ID.
GET include=watchers cần View watchers; valid explicit list chứa ID matched, thiếu ID mismatch;
missing/null/malformed/duplicate/read failure unavailable, không suy empty từ hidden expansion.
Matching không chứng minh call thêm membership mới; notification delivery không verify.
`remove_issue_watcher`: DELETE/api/v1/issues/{id}/watchers/{user_id}, hai positive IDs, không body/batch.
Cần Delete watchers và visibility, không thêm Add/Edit/View watchers. Một DELETE sau preflight;
native missing principal safe404,204 có thể removed hoặc no-op. Read-back explicit valid list
không ID matched, có mismatch, hidden/read404 unavailable. Accepted/uncertain giữ nguyên;
direct absence không chứng minh hết effective watching qua group/notification. No retry/rollback/atomic,
destructive true. Cả hai dùng outcome/upstream_accepted/issue_id/user_id/observed_present/verification.

## Lỗi :id=errors

### Kết quả ghi chưa chắc chắn :id=mutation-uncertainty

Mọi write gồm binary upload nhận native500..599 tạo uncertain receipt trong envelope REST200/MCP
hiện có, không chứng minh committed/failed. `outcome=uncertain`, upstream_accepted=null; create/upload
không invent ID/token, update/delete giữ known target. Adapter biết target có thể observation
matched/mismatch riêng, outcome vẫn uncertain; creation không reliable ID không speculative lookup.
Không parse/expose native5xx body hoặc tự retry. Batch membership giữ phase=executed, item uncertain,
verification unavailable và error write_outcome_uncertain, không read-back uncertain item; earlier
accepted giữ receipt, later not_executed; không thêm top-level outcome/upstream_accepted.
Auth/preflight GET5xx không dispatch mutation và giữ error contract. Failed read-back giữ receipt.
PREP-019 có offline/native Redmine 7.0.2 reconciliation/cleanup/Inspector bằng chứng riêng.

### Response lỗi đã loại dữ liệu nhạy cảm :id=sanitized-error-responses

| REST status | Mã/body | Ý nghĩa |
| --- | --- | --- |
| 401 | `{"detail":"Missing or invalid Redmine API key"}` | Thiếu/key bị từ chối |
| 422 | FastAPI detail | Input không hợp lệ |
| 403 | access_denied / permission_denied | Native/application policy từ chối |
| 404 | resource_not_found | Không tồn tại hoặc không visible |
| 401 | invalid_credentials | Native từ chối key sau initial identity check |
| 502 | upstream_unavailable | Transport lỗi; native GET503 cũng ánh xạ vào đây |
| 502 | upstream_rate_limited | Native429, bounded GET retry dừng/hết lượt |
| 503 | upstream_busy / service_unavailable | Không lấy connection kịp / runtime client chưa chạy/đã đóng |
| 502 | upstream_error / upstream_response | Status khác gồm redirect / JSON/data native sai |
| 502 | upstream_response_too_large | Decoded JSON vượt cap |
| 504 | upstream_timeout | Timeout, gồm native GET504 |
| 500 | internal_error | Lỗi bất ngờ, không expose chi tiết |

MCP có thể bọc tool error; không giả định cùng outer HTTP status. GET retry eligible connection/
read/write/timeout/remote-protocol failure và native429/502/503/504, mặc định tổng3attempts;
chỉ failed GET lặp, gồm auth/discovery/preflight/read-back. Malformed data/HTTP 500/pool/admission/
permission/budget không retry. Backoff/Retry-After/all attempts chia deadline/budget; không replay write.
Mỗi HTTP response có X-Request-ID. Lỗi sau streaming headers kết thúc stream, không thay bằng JSON.
Không expose upstream body/exception. `GET /health` không key, `{"status":"ok"}`, chỉ process
liveness, không Redmine connectivity/key check và không là MCP tool.

## Phụ lục ví dụ nguyên văn

Các đoạn mã/lệnh sau giữ nguyên từ bản gốc để tra cứu cú pháp. Không thực thi tự động; chỉ chạy bước kiểm thử hoặc mutation khi assignment cho phép.

```json
{"project_ids":[5,9],"limit":25,"offset":0}
```

```json
{"items":[{"project_id":5,"user_id":27,"role_ids":[2]}]}
```

```json
{"items":[{"project_id":5,"membership_id":101,"role_ids":[2,3]}]}
```

```json
{"items":[{"project_id":5,"membership_id":101}]}
```

```json
{"project_id": 10, "name": "sprint-01", "description": "First sprint", "due_date": "2026-10-20"}
```

```json
{
  "code": "version_already_exists",
  "message": "Creation was rejected; a version with this name already exists. The existing version is returned. Supplied fields were not applied."
}
```

```json
{"project_id": 3, "operation_id": "create_issue"}
```

```json
{"total_pages": 10000, "max_query_pages": 10, "requires_narrowing": true}
```

```json
{"limit": 25, "offset": 0}
```

```json
{"project_id": 1, "status_id": "*", "assigned_to_id": "me", "limit": 25, "offset": 0}
```

```json
{"project_id": 1, "tracker_id": 2, "parent_id": 3, "updated_since": "2026-01-01T00:00:00+07:00", "sort": "updated_on:desc"}
```

```json
{"project_id": 2, "category_id": 1, "status_id": "*", "limit": 100, "offset": 0}
```

```json
{"project_id": 5, "fixed_version_id": 2, "include_subprojects": false, "tracker_id": 1, "status_id": "*"}
```

```json
{"issue_id": 1}
```

```json
{
  "id": 2,
  "login": "demo-reader",
  "firstname": "Demo",
  "lastname": "Reader",
  "mail": null,
  "memberships": [
    {
      "id": 3,
      "project": {"id": 1, "name": "Demo"},
      "roles": [{"id": 4, "name": "Reporter", "inherited": false}]
    }
  ],
  "visibility": {
    "scope": "requesting_redmine_user",
    "observations": [{"path": "/mail", "state": "not_returned"}]
  }
}
```

```json
{
  "items": [
    {"id": 1, "identifier": "demo", "name": "Demo", "description": null, "status": 1, "parent": null}
  ],
  "total": 1,
  "limit": 25,
  "offset": 0,
  "visibility": {"scope": "requesting_redmine_user", "observations": []}
}
```

```json
{
  "items": [{"id": 9, "name": "Development"}],
  "visibility": {"scope": "requesting_redmine_user", "observations": []}
}
```

```json
{"issue_id": 488, "hours": 8, "spent_on": "2026-10-08", "activity_id": 9}
```

```json
{"issue_id":491,"time_entry_id":919,"hours":7.5,"comments":"Corrected hours"}
```

```json
{"outcome":"accepted","upstream_accepted":true,"resource_id":919,"issue_id":491,"verification":"not_found","observed_present":false}
```

```json
{
  "id": 1,
  "subject": "Example issue",
  "description": null,
  "project": {"id": 1, "name": "Demo"},
  "tracker": {"id": 1, "name": "Bug"},
  "status": {"id": 1, "name": "New"},
  "priority": {"id": 2, "name": "Normal"},
  "author": {"id": 2, "name": "Demo Reporter"},
  "assigned_to": null,
  "category": {"id": 1, "name": "BE"},
  "fixed_version": {"id": 2, "name": "Sprint 02"},
  "parent": null,
  "is_private": false,
  "done_ratio": 0,
  "start_date": "2026-09-03",
  "due_date": "2026-09-25",
  "spent_hours": 1.5,
  "total_spent_hours": 2.0,
  "created_on": "2026-01-01T00:00:00Z",
  "updated_on": "2026-01-01T00:00:00Z",
  "custom_fields": [],
  "journals": [],
  "attachments": [],
  "visibility": {
    "scope": "requesting_redmine_user",
    "observations": [
      {"path": "/allowed_statuses", "state": "not_requested"},
      {"path": "/changesets", "state": "not_requested"},
      {"path": "/children", "state": "not_requested"},
      {"path": "/relations", "state": "not_requested"},
      {"path": "/watchers", "state": "not_requested"}
    ]
  }
}
```

```json
{"spent_from":"2026-09-01","spent_to":"2026-09-30","limit":100,"offset":0}
```

```json
{"issue_to_id": 2, "relation_type": "blocks"}
```

```json
{"error": {"code": "resource_not_found", "message": "Resource unavailable or not visible"}}
```
