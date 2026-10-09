# Bằng chứng kiểm thử TOOL-042 :id=tool-042-testing-evidence

> Bản tiếng Việt được biên tập từ [tài liệu tiếng Anh gốc](#/docs/testing/evidence/tool-042-testing.md). Bản gốc là nguồn chuẩn cho hợp đồng và hồ sơ đầy đủ. Tên API, lệnh, ngày, waiver và giới hạn nghiệm thu được giữ nguyên; việc dịch không thực hiện kiểm thử.

**Ngày 2026-10-08**. Assignment cho phép viết/chạy test `update_time_entry`, thay giới hạn coding-only. TOOL-043 còn planned tại thời điểm record này; xem [evidence sau đó](tool-043-testing.md), giữ nguyên lịch sử.

## Phạm vi và môi trường :id=scope-and-environment

Offline dùng fake settings, MockTransport, ASGI lifespan và SDK thật, chặn transport mạng và xóa inherited settings. Owned Redmine 7.0.2 ở localhost 3001 được preflight pin/marker/volume/manifest. **Không đọc/sửa hoặc dùng incident #919–#924 và shared 6.0.5 cổng 3000 làm fixture**.

Helper tạo một private disposable project, bốn ordinary user/role, activity active/inactive và entry riêng. Không đổi baseline/global role/settings/activity/plugin/deployment. Private ledger và Inspector config ignored. Cleanup exact ownership xác nhận không còn project/entry/user/role/activity; config bị xóa và server tạm dừng.

## Traceability :id=test-implementation-and-traceability

| Scenario | Phạm vi |
| --- | --- |
| TOOL-042-001/002 | Strict partial input/null/empty/unknown, ID/hour/date/comment; exact issue-entry-project-user, malformed preflight zero PUT và omitted/control field |
| TOOL-042-003 | Credited user khác author; own/all/log-only/no-view; pinned/personal/gate/conditional permission |
| TOOL-042-004/005 | Native 204, rounding, mismatch/unavailable; pre-dispatch/dispatched/commit reply fault, một attempt, uncertainty |
| TOOL-042-006 | SDK schema/catalog/CSV/allowed_all/destructive hint và compatibility |
| TOOL-042-007/008 | Native REST/MCP/Inspector state/identity/aggregate/activity/control, role/policy và cleanup |
| TOOL-042-009 | Real PUT commit rồi inject reply loss/failed GET/intervening edit; không replay |

Shared activity-reader fixture không nghiệm thu hồi tố TOOL-040 waived. TOOL-041 vẫn cần testing riêng.

## Lệnh và kết quả :id=commands-and-results

| Lượt | Kết quả lịch sử |
| --- | --- |
| Initial focused | 335 pass/3 lỗi fixture |
| Full offline sau correction | 1.755 pass/1 lỗi argument reader cũ, 1.165,19 s |
| Bảy case muộn | 7 pass/92 deselected |
| Catalog case đã sửa | 1 pass/1,52 s, không giảm assertion |
| Initial owned live | 7 pass |
| Fault/current-settings bổ sung | 4 pass/6 deselected |
| Aggregate recheck | 2 pass/8 deselected |
| Final owned live | 10 pass/152,14 s, Inspector discovery/update |
| Static scoped | Ruff sáu task file + reader sửa, mypy 128 source và diff pass |

**Không có final clean full-offline rerun** sau case muộn/catalog correction. 61 unit và 99 integration riêng có passing evidence qua full + selected rerun; observed failure đã giải quyết. Giữ warning Pydantic và bảy Ruff finding/một format issue không liên quan từ coding handoff; không claim whole-repository clean.

## Findings và correction :id=findings-and-corrections

Lỗi đầu thuộc setup: đổi stored entry ID gây 404, pinned writer thiếu admitted user và capability URL fake sai. Case wrong-response-ID riêng chứng minh safe 502/zero PUT.

Native hiển thị 1,23 giờ từ stored 1,234 nhưng issue total là 2,234 nếu có control 1 giờ; sửa assertion, không cộng rounded display và **không đổi runtime**. Reader catalog test thiếu `project_id` TOOL-040 được sửa và rerun đúng case.

Native fault inject reply loss sau real PUT, không phải dropped TCP. Chỉ owned target bị GET failure/concurrent edit. Settings hiện tại cho phép future/closed time và empty comment, daily max 999; chỉ constraint thực sự bật mới claim reject. Không bao phủ mọi plugin/custom field/race hoặc global alternative policy. TOOL-042 complete trong scoped evidence, với lint baseline debt và các giới hạn giữ nguyên.

## Phụ lục ví dụ nguyên văn

Các đoạn mã/lệnh sau giữ nguyên từ bản gốc để tra cứu cú pháp. Không thực thi tự động; chỉ chạy bước kiểm thử hoặc mutation khi assignment cho phép.

```bash
uv run --frozen --no-sync pytest tests/unit/test_time_entry_updates.py tests/integration/test_time_entry_updates.py tests/integration/test_current_tools.py -q --tb=short
uv run --frozen --no-sync pytest tests/unit tests/integration -q --tb=short
uv run --frozen --no-sync pytest tests/integration/test_time_entry_updates.py -q --tb=short -k 'inaccessible_preflight or wrong_response_identity or incomplete_role'
uv run --frozen --no-sync pytest tests/integration/test_reader_contracts.py::test_user_005_009_all_reader_mcp_invocation_and_sanitized_errors -q --tb=short
uv run --frozen --no-sync pytest tests/e2e/test_time_entry_update_acceptance.py --run-e2e -q --tb=short
uv run --frozen --no-sync pytest tests/e2e/test_time_entry_update_acceptance.py --run-e2e -q --tb=short -k 'commit_faults or current_settings'
uv run --frozen --no-sync pytest tests/e2e/test_time_entry_update_acceptance.py --run-e2e -q --tb=short -k native_update_state
uv run --frozen --no-sync mypy src
git diff --check
```

```bash
test_files=(
  tests/unit/test_time_entry_updates.py
  tests/integration/test_time_entry_updates.py
  tests/integration/test_current_tools.py
  tests/integration/conftest.py
  tests/e2e/test_time_entry_update_acceptance.py
  tests/e2e/server.py
)
uv run --frozen --no-sync ruff check "${test_files[@]}"
uv run --frozen --no-sync ruff format --check "${test_files[@]}"
uv run --frozen --no-sync ruff check tests/integration/test_reader_contracts.py
uv run --frozen --no-sync ruff format --check tests/integration/test_reader_contracts.py
```
