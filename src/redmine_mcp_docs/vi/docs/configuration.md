# Cấu hình :id=configuration

> Bản tiếng Việt được biên tập từ [tài liệu tiếng Anh gốc](#/docs/configuration.md). Bản gốc là nguồn chuẩn cho hợp đồng và hồ sơ đầy đủ. Tên API, lệnh, ngày, waiver và giới hạn nghiệm thu được giữ nguyên; việc dịch không thực hiện kiểm thử.

## Cấu hình runtime :id=runtime-settings

Settings được tạo khi `create_app()` chạy. Local đọc `.env` theo working directory, nên chạy
từ root repository. Process environment ưu tiên hơn `.env`; dotenv entry không liên quan bị bỏ qua.
URL phải HTTP/HTTPS, có thể có subpath nhưng không embedded credential/query/fragment.
Giá trị bắt buộc sai khiến startup thất bại. `REDMINE_API_KEY`/`MCP_API_TOKEN` là runtime setting đã
ngừng dùng, cần xóa khỏi external env; setup synthetic xóa khỏi marked `.env`.

| Biến | Mặc định | Mục đích/điều kiện |
| --- | --- | --- |
| REDMINE_URL | Bắt buộc | Base URL mà MCP truy cập được |
| REDMINE_WRITE_ENABLED | false | Writer riêng; Compose reader luôn false, writer profile true |
| REDMINE_WRITER_AUTH_MODE | pinned_key | Một key ghim; personal_key xác thực key riêng từng caller |
| REDMINE_WRITER_USER_IDS | Rỗng | CSV integer dương, bắt buộc pinned writer; personal optional chỉ giới hạn ghi |
| REDMINE_WRITER_OPERATIONS | Rỗng | Write IDs CSV hoặc allowed_all độc lập; rỗng không mutation, ID sai/mixed allowed_all lỗi startup |
| REDMINE_WRITER_KEY_SHA256 | Rỗng | Digest SHA256 lowercase riêng, bắt buộc pinned; phải rỗng personal |
| REDMINE_TIMEOUT_SECONDS | 20 | Read/write inactivity timeout dương hữu hạn, không end-to-end deadline |
| REDMINE_CONNECT_TIMEOUT_SECONDS | 5 | Connection timeout dương hữu hạn |
| REDMINE_POOL_TIMEOUT_SECONDS | 5 | Pool acquisition timeout dương hữu hạn |
| REDMINE_REQUEST_DEADLINE_SECONDS | 60 | Deadline một upstream read gồm retry/backoff/wait/stream/close |
| REDMINE_READ_RETRY_MAX_ATTEMPTS | 3 | Tổng GET attempts 1..5; 1 tắt retry, mutation vẫn một lần |
| REDMINE_READ_RETRY_BASE_DELAY_SECONDS | 0.5 | Exponential backoff base dương hữu hạn, <=max delay |
| REDMINE_READ_RETRY_MAX_DELAY_SECONDS | 5 | Delay cap dương hữu hạn; Retry-After lớn hơn cap kết thúc retry |
| REDMINE_MAX_RESPONSE_BYTES | 10485760 | Cap decoded JSON mỗi read, dương |
| REDMINE_MAX_BINARY_BYTES | 5242880 | Upload decoded cap5MiB, dương; download content tắt |
| REDMINE_MAX_REQUEST_BODY_BYTES | Derived, hiện10485760 | Optional positive REST/MCP admission cap; bỏ qua để derive, không gán rỗng |
| REDMINE_MAX_CONNECTIONS | 100 | Shared upstream connection cap dương |
| REDMINE_MAX_KEEPALIVE_CONNECTIONS | 20 | Idle cap không âm và <=max connections |
| REDMINE_MAX_CONCURRENT_REQUESTS | 50 | Semaphore physical request chung theo process |
| REDMINE_ADMISSION_TIMEOUT_SECONDS | 30 | Max permit wait dương hữu hạn, hết=>503 upstream_busy trước dispatch |
| REDMINE_MAX_QUERY_PAGES | 10 | Stateless matching-page/continuation ceiling dương |
| REDMINE_READ_OPERATION_MAX_REQUESTS | 30 | Logical reader attempt budget gồm auth/probe |
| REDMINE_READ_OPERATION_DEADLINE_SECONDS | 90 | Deadline reader gồm admission/acquisition/conversion |
| REDMINE_READ_OPERATION_MAX_BYTES | 10485760 | Aggregate decoded response budget reader |
| REDMINE_MEMBERSHIP_BATCH_MAX_REQUESTS | 300 | Mọi physical request trong một write batch, gồm mutation |
| REDMINE_MEMBERSHIP_BATCH_MAX_READ_BYTES | 31457280 | GET bytes budget30MiB, write response vẫn per-response cap |
| REDMINE_MEMBERSHIP_BATCH_DEADLINE_SECONDS | 300 | Deadline phối hợp cho toàn membership batch |
| REDMINE_PUBLIC_URL | Không đặt | Browser-facing origin/subpath cho attachment link hợp lệ |
| LOG_LEVEL | INFO | DEBUG/INFO/WARNING/ERROR/CRITICAL, không phân biệt hoa thường |

Request-body admission áp dụng MCP POST và REST POST/PUT/PATCH/DELETE `/api/v1/`, cả internal ASGI.
Derived cap `max(REDMINE_MAX_RESPONSE_BYTES, 4 * ceil(REDMINE_MAX_BINARY_BYTES / 3) + 65536)`:
base64+64KiB đủ ordinary compact JSON, không bảo đảm escaping/padding tùy ý. Binary decoded/service
encoded limit độc lập. Base Compose **không forward optional body cap**: chỉ thêm vào --env-file
không cấu hình container; cần environment override rõ ràng. Local Python đọc process/.env.
Content-Length thiếu/chunked được; malformed/negative/conflicting/mismatch =>400 invalid_request_body,
actual oversize ưu tiên=>413 request_body_too_large, non-identity Content-Encoding=>415 request_encoding_unsupported.
Không decode compressed; reject trước parser/auth/mutation. Outer MCP là HTTP transport error không
CallToolResult, internal REST giữ tool-error conversion. Chỉ body accepted đầy đủ replay downstream,
stop oversized chunk/disconnect, giữ GET/SSE/session DELETE/cancel/stream behavior. Cap không phải total
process-memory/concurrent-load guarantee. [PREP-024 evidence](testing/evidence/prep-022-026-testing.md).

Mọi REST/MCP request mang đúng một X-Redmine-API-Key, verify users/current.json rồi upstream cùng key.
Không persist/log key; reject repeated/>512chars/internal whitespace/nonASCII/control401,
trim whitespace ngoài. Pool không dùng cookie hoặc default authorization chung.
Response có server-generated X-Request-ID, safe timing/status/error logs không input/upstreamcontent;
retry event chỉ attempt/next/delay/native status/allowlisted reason.

GET retry connection/read/write/timeout/remoteprotocol và native429/502/503/504, default3total.
HTTP 500/invalid JSON-model/oversize/pool-admission/permission/budget-deadline không retry.
Auth/discovery/page/preflight/read-back thuộc policy; không whole-tool/internaldispatch/batch/mutation
replay. Default jitter wait0.25..0.5s rồi0.5..1s. Một Retry-After integer/date hợp lệ kéo dài wait;
header lặp/sai dùng backoff, trên cap hoặc không đủ remaining deadline giữ current mapped error.
Đóng response/release capacity trước wait, không consume error body; attempt/partial decoded byte
đều tính budget. Deadline acquisition mỗi GET riêng, không toàn invocation/stream; parsing sau đó,
retry không reset deadline, clipping theo aggregate absolute monotonic cutoff. Cap buffer không bảo đảm
memory decompressor/parser; oversized=>502 upstream_response_too_large.

REST reader budget bắt đầu trước auth, MCP internal share read-tool budget; dispatch/discovery tạo
fresh scope để tránh expired session context, writer xóa inherited reader budget. Membership batch
có scope cooperative riêng; in-flight mutation timeout không bị đổi, external cancel truyền tiếp.
Sync conversion hết deadline trước headers=>504 read_operation_timeout; sau headers kết thúc stream.
HTTPX ASGI inactivity timeout+5s không phải whole-tool timer; explicit reader/capability/batch scopes
mới giới hạn work. Both Compose services forward READ_RETRY settings, thay live config là thao tác riêng.

Proxy HTTP_PROXY/HTTPS_PROXY/ALL_PROXY/NO_PROXY theo process/platform HTTPX; .env app không tự
load arbitrary proxy env, Docker cần forward rõ ràng. Direct/proxy share semaphore tới response close.
Cap là simultaneous physical calls, không rate/fairness/quota; mỗi worker/reader/writer process có
semaphore riêng, combined load có thể vượt một process cap. Không persistent query state/cache/token.
Pagination ceil(total/requested_limit): offset0 large preview requires_narrowing; positive offset kiểm
offset+limit<=max_pages*limit, same-filter probe offset0limit1 trước fetch. Counts vẫn native và có thể
tốn chi phí. Scope lớn/growing=>422 scope_required. Download retired403 trước auth/upstream;
browser metadata link với public URL, cần native login/permissions. Visibility chỉ caller, omissions
không giải thích tại sao hoặc phát hiện hidden records.

## Môi trường tổng hợp :id=synthetic-environment

`bash scripts/dev-up.sh` tạo random `.env` nếu thiếu; không copy .env.example cho synthetic.
Config existing phải mang marker, tách real-instance config. POSTGRES_PASSWORD/TEST_USER_PASSWORD
và REDMINE_SECRET_KEY_BASE được tạo riêng (Rails nhận cả SECRET_KEY_BASE).
REDMINE_TEST_MARKER phải `redmine-mcp-synthetic-v1`, kèm local state check trước destructive helper.
Database/user là redmine. Key seed ở ignored .local/credentials.json, không .env. Inspector lấy
personal key kín từ account page/credential file. Credential/manifest/backup/generated state ở .local.

## Địa chỉ local và Docker :id=local-and-docker-addresses

| Caller | Redmine URL |
| --- | --- |
| Python local với synthetic | http://localhost:3000 |
| MCP container synthetic override | http://redmine:3000 |
| Container tới Windows host | http://host.docker.internal:<port> |

Base Compose forward runtime interpolation env; synthetic override đổi REDMINE_URL sang service.
Shell env có thể override --env-file, tránh stale exported credential. Published localhost:
MCP8000(MCP_HOST_PORT), Redmine3000, PostgreSQL5433; MCP bên trong vẫn8000, PostgreSQL5432.
MCP không kết nối PostgreSQL. Dừng MCP container trước local Python cùng8000.

## Redmine bên ngoài :id=external-redmine

```bash
mkdir -p .local
cp -n .env.example .local/external.env
```

Sửa file riêng tư với actual URL, dùng base Compose runtime settings; synthetic DB/account config
không cấu hình Redmine bên ngoài. Chạy theo [vận hành](operations.md). Không seed/reset/restore
external, không disable TLS verification, không chia sẻ docker compose config vì interpolation lộ secret.

## Writer deployment riêng :id=separate-writer-deployment

Base Compose mcp-server luôn read-only; opt-in mcp-writer localhost8001(MCP_WRITER_HOST_PORT).
Chuẩn bị file riêng, không start deployment:

```bash
mkdir -p .local
cp -n .env.example .local/writer.env
chmod 600 .local/writer.env
```

Pinned: actual URL, WRITE_ENABLED=true, AUTH_MODE=pinned_key, ordinary positive USER_IDS và private
KEY_SHA256; để operation rỗng đến khi chọn scope. Không thay reader config. Local writer cần explicit
write gate, Compose writer forces true. Digest không đặt key trong argument/history:

```bash
read -rs writer_key; printf '\n'
printf '%s' "$writer_key" | sha256sum | cut -d ' ' -f 1
unset writer_key
```

Dùng dedicated ordinary user tối thiểu quyền, không admin key. Digest so trước nativecall,
key khác401, user không khớp403 cho REST/MCP; restricted caller vẫn thấy read. Multi-caller:

```bash
REDMINE_WRITER_AUTH_MODE=personal_key
REDMINE_WRITER_KEY_SHA256=
REDMINE_WRITER_USER_IDS=
```

Mỗi caller key riêng; USER_IDS optional chỉ hạn chế write, excluded valid user vẫn read/connect.
Rỗng không grant native permission. Rollback chọn pinned +validdigest/IDs, reconnect client.
Mọi MCP HTTP request reauthenticate; SDK1.30.0 session bind userID/issuer/private key fingerprint,
user/key khác cùng404 unknown-session, keyrotation cần session mới; cleanup khi termination/expiry/shutdown.
Không return/log fingerprint. Personal write dùng caller memberships/role permission theo target thật;
known absent permission403, present conditional, missing/inaccessible unknown không grant/denial;
malformed/timeout/transport safeerror stop. Không role-name mapping/admin substitution/cross-request cache.
Discovery giữ allreads, gate ceiling/admission, chỉ hide write proved unavailable từ complete inventory.
Visible inventory page100 bounded query/read budget, partial/changing không prove denial. Invocation
cached/direct vẫn REST target auth; re-list refresh, không list-change notification guarantee;
copies không mutate superset schema cache user khác.

```bash
REDMINE_WRITER_OPERATIONS=allowed_all
```

Lowercase độc lập (trim outer whitespace), expands toàn WRITE_OPERATIONS cho discovery/REST/capability,
gồm registration mới sau upgrade. ExplicitCSV giữ fixedscope. Gate/key/nativepermissions vẫn cần.
Đổi env-file phải **recreate Compose writer**, plain restart giữ env container cũ; local restart với env
mới, reconnect/re-list. Có thể chỉ allow membership add/update/delete hoặc create_project_version,
ordinary caller manage_members/manage_versions target; role constraints native. Version read-back cần
view_issues nhưng creation không cần. Operation rỗng zero writes; unknownID startupfail; require_write_access
mọi route; readerREST403. Catalog18writes. Creation time entry cần log_time/visibleissue/dateexplicit,
activity default native, view_time_entries cho discovery/GET, testing pending. Update/delete cần visible
entry/issue, view_time_entries+edit_time_entries hoặc eligible edit_own_time_entries theo credited user,
log_time không đủ; không reassignment. [TOOL-042](testing/evidence/tool-042-testing.md)/[043](testing/evidence/tool-043-testing.md)
có owned acceptance scoped, không chỉnh deployed configuration.

Write một attempt, body/responsebounded, native success validation; dispatched uncertain giữ target known,
create/upload không invent ID/token. **Mọi native500..599 đều uncertain**, không opt-in/switch;
observations độc lập không thành acceptance, không parse/expose errorbody. Failed preflight zero mutation,
failed GET giữ receipt, no retry/rollback. Membership native 200/204 empty accepted, batch5xx phaseexecuted,
item uncertain/verification unavailable/write_outcome_uncertain, earlier giữ, laternot_executed;
không batch-wide acceptancefield. [PREP-019](plans/tasks/prep-019-write-outcome-consistency.md)
ghi offline/Redmine 7.0.2 thuộc sở hữu reconciliation/Inspector compatibility, config không tự establish acceptance.
