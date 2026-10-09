# Bằng chứng kiểm thử retry PREP-027 :id=prep-027-retry-verification

> Bản tiếng Việt được biên tập từ [tài liệu tiếng Anh gốc](#/docs/testing/evidence/prep-027-testing.md). Bản gốc là nguồn chuẩn cho hợp đồng và hồ sơ đầy đủ. Tên API, lệnh, ngày, waiver và giới hạn nghiệm thu được giữ nguyên; việc dịch không thực hiện kiểm thử.

**Ngày 2026-10-07**, testing được giao sau implementation/static checks. Working tree có PREP-027 và bug/index edit trước đó. Không commit, deploy, reset hoặc seed.

## Phạm vi và môi trường :id=scope-and-environment

Offline dùng locked pytest/asyncio, MockTransport, admitted transport, ASGI lifespan và SDK session thật; chặn real network và production dotenv/key. Owned `redmine-mcp-e2e` ghim 7.0.2 ở localhost 3001 được preflight pin/marker/Compose/volume/manifest. Inspector 2.8.0 đã cache chạy offline, reader tạm ở 18087 và finally dừng/xóa private config. Live chỉ đọc: **không mutation hoặc tạo fixture**, giữ volume/data. Fault recovery và writer uncertainty được kiểm tra offline.

## Mapping kịch bản :id=tests-and-scenario-mapping

TEST-001/002/004 kiểm eligible exception/status, recovery/exhaustion và noneligible/malformed payload. TEST-003 kiểm charge từng attempt/partial stream/request-byte exhaustion. TEST-005/006 kiểm default/disabled/settings/Compose và Retry-After/cap/jitter. TEST-007 kiểm cancel, close, permit cleanup và deadline. TEST-008 kiểm concurrent key/cookie isolation/safe log. TEST-009 kiểm REST/MCP identity/detail/discovery/error/probe và một dispatch. TEST-010/012 kiểm mutation JSON/binary một lần, preflight/read-back GET, batch cutoff và internal timing. TEST-011 đối chiếu owned native/catalog/startup/Inspector ba read.

Deterministic helper quan sát call/close/counter/result; không replay cả tool. Runtime retry không thay đổi trong testing stage.

## Execution :id=execution-record

| Lượt | Kết quả |
| --- | --- |
| Focused offline | 103 pass, gồm invalid JSON thật sự tới parser |
| Adapted reader contracts | 81 pass/144 deselected |
| Full offline | 1.457 pass/41 lỗi expectation một attempt cũ; không clean full run |
| Legacy foundation targeted | 11 pass/52 deselected |
| Owned live reader | 2 pass |
| Startup/Inspector | Discovery + ba read pass, 0 mutation |
| Static lịch sử | Ruff/format 284 file, mypy/architecture 124 source/module và whitespace pass |

## Sửa lỗi và giới hạn :id=corrections-and-limitations

Fixture được sửa ở stream closure, filename, watcher fake và SDK client import/attribute. Các expectation 429/503/504/profile timeout cũ đổi sang ba GET với auth một lần, giữ URL/expansion; noneligible vẫn một attempt. Hai function foundation chọn một attempt để kiểm transport mapping/body closure, còn default retry có case riêng.

Full run collect 1.498 = 1.457 pass + 41 fail. Final targeted **92 parameterization của năm function đã sửa pass**, XML đối chiếu mọi 41 failure với passing rerun; không unresolved failure. **Không rerun full suite sau test-only edit**. Lượt full bị ngắt trước đó không là acceptance; wrapper parse error sau pytest được tách khỏi JUnit hoàn tất.

Giữ warning Pydantic và 18 warning `record_property`/xunit2 có trước. Native chỉ chứng minh read compatibility; không live fault/mutation, production fault, build/recovery/release. PREP-027 complete theo combined full + targeted/focused/live/Inspector/static evidence. BUG-001 malformed-payload sanitization vẫn cần evidence riêng.

## Sửa cleanup credential Inspector :id=follow-up-review-fix-inspector-credential-cleanup

Ngày **2026-10-07**, P2 finding được giao riêng. Outer try/finally sở hữu việc xóa credential từ trước verification, gồm partial write/chmod/log open/process launch; shutdown terminate/wait/kill không bỏ qua delete. Error vẫn propagate, không giả pass. Runtime retry không đổi.

Unit cleanup **9 pass** (tám failure path + success) dùng file tạm/mock HTTP/subprocess, không launch native/Docker/server/Inspector. File-based import sửa collection error do module có dấu gạch nối. Scoped Ruff/mypy/diff pass; không rerun full/live/Inspector cho harness-only fix.
