# Kiểm thử regression preparation :id=preparation-regression-testing

> Bản tiếng Việt được biên tập từ [tài liệu tiếng Anh gốc](#/docs/testing/evidence/prep-022-026-testing.md). Bản gốc là nguồn chuẩn cho hợp đồng và hồ sơ đầy đủ. Tên API, lệnh, ngày, waiver và giới hạn nghiệm thu được giữ nguyên; việc dịch không thực hiện kiểm thử.

Người dùng giao viết/chạy kiểm thử PREP-022–026 ngày **2026-10-07**, thay handoff chỉ coding trước đó. Phạm vi gồm offline, Redmine 7.0.2 được ghim thuộc sở hữu, startup/shutdown và Inspector 2.8.0. Không gồm deployment, CI hoặc recovery.

## Coverage :id=coverage

| Nhóm scenario | Nội dung |
| --- | --- |
| SCHEMA-022-001–007 | SDK union integer/me/null, version nullable, canonical constraints/reference/examples, cache/session isolation, writer receipt, native clear assignment và Inspector |
| BATCH-023-001–006 | REST/MCP add/update/delete 1/2/10 item, một mutation mỗi item, physical request count, dedicated budget/deadline, target/permission thay đổi, failed GET, cancel và ordinary-manager native cleanup |
| BODY-024-001–006 | Declared/streamed oversize, Content-Length/framing/encoding, exact cap/chunk/early stop, N−1/N/N+1 upload, replay một lần, pre-auth reject, session/cancel và owned Inspector upload |
| FIELD-025-001–006 | Strict root/nested/receipt ID, boolean/count/progress/delay/status; null/default/date/hour policy, malformed preflight zero write, malformed GET giữ receipt, native parity |
| SDK-026-001–006 | Source isolation/pinned version/hook shape, safe startup failure, schema/cache/discovery/session, DELETE JSON/budget/uncertainty, readiness/cancel/shutdown/client cleanup |

Các mã trong bản gốc xác định từng case chi tiết; bảng này tổ chức theo nhóm.

## Lỗi được phát hiện và sửa :id=defects-exposed-and-corrected

SDK 1.30.0 mặc định cap HTTP 4 MiB làm upload base64 từ file 5 MiB hợp lệ bị 413. Facade truyền effective application body cap vào session manager; outer admission vẫn trước auth/parse.

Redmine 7.0.2 bỏ JSON null `assigned_to_id`; gateway create/copy/update chuyển explicit null thành native empty string để clear, giữ expected-state null. Field bị omit vẫn omit; numeric/me không đổi.

Sáu baseline test được cập nhật từ read deadline 90 s sang dedicated batch budget và từ patch adapter cũ sang compatibility boundary với object thật. Không dùng kết quả initial failure làm acceptance.

## Fixture riêng :id=owned-fixture-handling

Preflight kiểm image/container/Compose/volume version-owner và manifest riêng tư. Tool write dùng ordinary key; admin chỉ prepare/cleanup fixture. Prefix duy nhất và exact ownership được kiểm trước delete; native absence được đối chiếu sau. Upload được gắn vào disposable issue để cleanup; không giả định DELETE attachment xóa được unattached upload. Artifact gián đoạn chỉ được xử lý theo filename, caller và môi trường marker/pin chính xác. Không reset hoặc đổi grant chung.

## Tái thực hiện :id=reproduction

Các command literal từ bản gốc được giữ ở phụ lục dưới. Chỉ chạy trong assignment cho phép, dùng Git Bash và locked dependencies. Live suite gọi Inspector/native, dừng app tạm và cleanup project/role/issue/attachment riêng. Secret/config/raw log nằm trong `.local/` ignored.

## Kết quả execution :id=execution-results

Final owned live **23 pass/246,84 s**; final full offline **1.395 pass/724,39 s**, không failure/skip. Physical count add/update là **75 REST/85 MCP**, delete **74 REST/84 MCP**, gồm admission/discovery ngoài batch context; một mutation mỗi item, dưới cap 300 request.

Ruff/format 273 Python file, mypy 123 runtime file, architecture và diff checks pass. Warning Pydantic có trước được giữ. Initial baseline 1.080 pass/6 obsolete-fixture failure và targeted run phát hiện hai runtime defect không phải acceptance; kết quả cuối đã sửa mới là evidence. Tăng 309 offline và 2 live so với baseline 1.086/21.

Byte admission/early stop không đo mọi ASGI process-memory hoặc production load. Ngưỡng coverage, CI, toàn bộ historical permission matrix và production readiness hoãn. Private XML/log/native cleanup không commit. Không rerun khi dịch trang này.

## Phụ lục ví dụ nguyên văn

Các đoạn mã/lệnh sau giữ nguyên từ bản gốc để tra cứu cú pháp. Không thực thi tự động; chỉ chạy bước kiểm thử hoặc mutation khi assignment cho phép.

```bash
uv run --no-sync pytest -q
bash scripts/check.sh
uv run --no-sync python scripts/prepare-e2e.py
uv run --no-sync pytest -q tests/e2e --run-e2e
```
