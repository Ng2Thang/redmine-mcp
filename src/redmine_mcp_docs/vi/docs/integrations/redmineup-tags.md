# Issue tags qua REST hiện có :id=issue-tags-through-existing-rest

> Bản tiếng Việt được biên tập từ [tài liệu tiếng Anh gốc](#/docs/integrations/redmineup-tags.md). Bản gốc là nguồn chuẩn cho hợp đồng và hồ sơ đầy đủ. Tên API, lệnh, ngày, waiver và giới hạn nghiệm thu được giữ nguyên; việc dịch không thực hiện kiểm thử.

Chỉ dùng REST API server hiện có. Không cài plugin, sửa code/config hoặc restart Redmine. Companion approach cũ đã bỏ; task không cài thêm gì lên server.

## Hành vi hiện tại :id=current-behavior

`get_issue` giữ GET `issues/{id}.json` cùng key/include/visibility/budget. Detail có `tags` nullable read-only nếu upstream cung cấp; list/writer observations không đổi. Không thêm endpoint phụ hoặc configuration flag. String array được giữ tên và ordinal sort; blank/duplicate/non-string bị safe 502 `upstream_response`. `[]` cho biết không có assignment; omitted hoặc null trả unavailable evidence, không tự kết luận empty/denial.

## Bằng chứng REST người dùng cung cấp — 2026-10-08 :id=user-supplied-rest-evidence-2026-10-08

Đây là observation người dùng gửi, không agent test hoặc full MCP acceptance. Chỉ ghi ID/count/field presence, không body/key riêng tư.

| ID | Điều kiện | Kết quả |
| --- | --- | --- |
| TAGS-REST-001 | Project list, structured `issue_tags=notification`, open | ID 489/488, total 2, offset 0, limit 25; filter match nhưng không tag array |
| TAGS-REST-002 | Cùng query, tên không tồn tại | Empty/total 0; cùng positive control xác nhận single-known-name filter trên server đó |
| TAGS-REST-003 | GET issue 489 | Không `tags`/`tag_list`/`issue_tags`; không expose đầy đủ assignment |

Native dùng fields/operators/values, `issue_tags` operator `=` và status operator `o`. User sample dùng project path; MCP dùng top-level `issues.json` với numeric project ID. Sample chưa xác nhận multi-tag ANY overlap, subproject/private role, continuation, special name hoặc mutation permission.

## Mapping từ source ghim :id=query-mapping-from-versioned-source

IssuesController index dùng cùng IssueQuery cho HTML/API. Query build nhận fields/operators/values hoặc f/op/v; có `fields[]` sẽ xóa short filter, nên MCP chuyển **mọi core filter** sang structured format để không mất filter. Project/include/limit/offset/sort vẫn top-level.

Tags 2.2.0 query patch dùng `issue_tags`, operator `=`, `any:true` và repeated values. Native visibility/filter chạy trước count/page. Source hỗ trợ ANY, nhưng sample chỉ một tên. Gem 1.1.12 dùng SQL LIKE; chặn `%`, `_` và backslash để literal không thành wildcard. Core short filter split `|`, nên dùng array. TOOL-036 không env switch/probe/server change.

## Giới hạn khả dụng :id=availability-limitation

Ngày **2026-10-08**, người dùng bỏ tag writer/name creation khỏi roadmap. Source permission edit/create tags không chứng minh effective write preflight hoặc bảo toàn assignment concurrent. Không có MCP tag writer.

Core 7.0.2 và Tags 2.2.0 Light không serialize tags detail JSON; mapper chỉ giữ field nếu existing response thật sự có. Không giả định undocumented endpoint, UI autocomplete, parse field giả định hoặc direct database. Không suy ra full tags từ filter ANY: match không chứng minh mọi requested tag hoặc không có tag khác. Known-name filtering tách khỏi full assignment/vocabulary.

## Bằng chứng source :id=source-evidence

Source inspection ngày **2026-10-08**, không execute vendor code; artifact nằm trong ignored `.local/vendor/`.

| Artifact | SHA256 |
| --- | --- |
| User Tags 2.2.0 Light ZIP | `242a7e348acd80544e89a0e461cfeb55c0ccfa85be1b9a1bfdb058dd6f875eae` |
| Local Redmine 7.0.2 archive | `d45e6d4c373cc3c8d33f1f4d4a2ffae1e1adb18703160707467493de7b4be591` |
| Public redmineup 1.1.12 gem | `70804375f39021ff28ed0bfd68923a3a6f3d9a9a1bc180224996b319f644cf2c` |

Core serializer và plugin route/library không có extension để trả full tags; internal association không cấp REST hoặc database permission. Coding handoff PREP-028/TOOL-036 không tự chạy verification. Sau đó TOOL-036 testing được giao: **82 focused offline/3 selected live Redmine 6.0.5 cổng 3000/Inspector discovery + hai call pass**, theo [record tiếng Anh](../testing/evidence/tool-036-tag-filter-testing.md). Full 7.0.2/real overlap/private role/PREP-028 mapper acceptance còn pending; không deployment/plugin/fixture mutation.
