# Phát triển :id=development

> Bản tiếng Việt được biên tập từ [tài liệu tiếng Anh gốc](#/docs/development.md). Bản gốc là nguồn chuẩn cho hợp đồng và hồ sơ đầy đủ. Tên API, lệnh, ngày, waiver và giới hạn nghiệm thu được giữ nguyên; việc dịch không thực hiện kiểm thử.

Reader vẫn read-only. Writer nhiều caller dùng `personal_key`, không pinned digest và có thể giới hạn write-user ID. Pinned mode mặc định nhận một key. Mỗi caller giữ key riêng; xem [cấu hình](configuration.md).

## Môi trường :id=environment

Dùng Python 3.13, uv và Git Bash Windows từ repository root. `.python-version` chọn minor, `pyproject.toml` giới hạn runtime 3.13. Doctor kiểm prerequisite bắt buộc và báo Docker/Node tùy chọn; không đọc secret `.env`, cài package, gọi service hoặc sửa file. Các command nguyên văn ở phụ lục. Dừng Docker MCP trước khi chạy local 8000. Settings được tạo lúc app creation; client theo lifespan; import không đọc credential/gọi mạng.

## Xử lý đồng thời :id=request-concurrency

REST/gateway async, shared AsyncClient dùng connection pool chung nhưng key theo request. Khi chờ Redmine, Uvicorn xử lý request khác; MCP dùng cùng route. I/O trong handler phải async. Nếu thêm CPU-heavy work, đo trước rồi offload đúng phần cần thiết, không chuyển cả async request vào worker thread.

## Check chất lượng :id=quality-checks

Chỉ chạy khi assignment cho phép. `scripts/check.sh` chạy cả bốn check: whole-repository Ruff lint/format, runtime mypy và architecture import checker, kể cả một check fail; exit nonzero nếu có failure. Không rewrite source hoặc cần Docker/key. Frozen uv có thể cài dependency locked còn thiếu. Ruff là công cụ chính, mypy strict cấu hình trong pyproject; Flake8 chỉ compatibility tùy chọn. Python line limit 100; EditorConfig/Git attributes quản lý whitespace/line ending. Codecov status/comment tắt, không tự collect/upload coverage.

### Pre-commit tùy chọn :id=optional-pre-commit-hooks

Cài dependency không cài hook. Validate/install/run chỉ khi opt-in. Hook chạy Ruff lint/format/mypy theo full scope một lần, không autoformat hoặc chỉ staged filename. Architecture nằm trong `check.sh`, không trong hook. uv phải trên PATH. Pre-commit có thể stash unstaged tracked changes tạm; không mandatory CI.

## Duy trì compatibility MCP đã ghim :id=maintain-the-pinned-mcp-compatibility-boundary

FastAPI-MCP 0.4.0/MCP SDK 1.30.0 là supported pair. `compatibility.py` sở hữu private request/transport/cache/handler/manager/lifecycle; policy gọi typed facade, không trực tiếp private attribute. Kiểm trước install, sau mount và trước startup; fail safe, không relax auth hoặc fallback cài version khác.

Upgrade là task riêng: đối chiếu versioned source/signature, cập nhật pin + lock, facade check và giữ schema/hint/cache/discovery/budget/mount ordering. SDK-026-001–006 có verification riêng cho bad hook/version, union/null, caller/session, DELETE JSON, receipt/budget/readiness/cancel/shutdown. Fault patch vào compatibility boundary, không partial namespace chưa kiểm. Static pass không runtime acceptance; [evidence](testing/evidence/prep-022-026-testing.md) thay handoff coding-only lịch sử. SDK cap khớp app; explicit null assignee map native empty ID, omit giữ nguyên.

## Thêm reader :id=add-a-read-only-tool

1. Tạo typed request/response/query và Protocol port trong feature.
2. Service kiểm nghiệp vụ trước port, giữ router → service → port → gateway. Không FastAPI/HTTPX ngoài status-constant exception.
3. Gateway dùng async pool không credential và safe errors trong integrations; MCP không PostgreSQL.
4. Bootstrap gắn dependency cụ thể, router nhận service qua dependency.
5. REST GET `/api/v1` có stable unique `operation_id`, personal key và `require_read_access`; đăng ký trước MCP và thêm explicit catalog. Startup từ chối route/schema/auth mismatch.
6. Cập nhật tool reference/config/changelog, giữ tên công cụ đang có.
7. Check/test/startup/Inspector/live theo phạm vi được giao; documentation review chỉ đọc source/prose/link, ghi deferred/limitation.

Package initializer có `__all__` rõ ràng; external dùng public package import, internal có thể direct import để tránh vòng khởi tạo. Feature export model/port/query/service, không router trong initializer. Root factory lazy import; checker resolve re-export theo ownership. `tools.seed` import không tự seed.

Dùng `http_status.HTTP_*` cho status, không đổi số pagination thành hằng HTTP. Strict query, named port argument và validation cả direct-service call. Bắt đầu từ outcome/dashboard thay generic CRUD proxy. Writer task phải định side effect, native permission, deployment/operation gate, single-attempt uncertainty, read-back và owned cleanup; `allowed_all` có thể bật writer tương lai, CSV là ceiling cố định.

## Hằng text dùng chung :id=shared-text-constants

Error/message/code/log nằm trong `constants/`, dùng `Final[str]` và nhóm theo trách nhiệm. Description tool/parameter giữ inline ở router, response description cạnh model. Dynamic message dùng named format; log dùng format + argument riêng, không interpolate key/body/native content. Constants không import runtime/framework; field/URL/permission/schema/default vẫn ở contract. Review wording và stable code tại mọi consumer khi thay đổi.

## Bảo trì portal :id=documentation-portal-maintenance

Canonical tiếng Anh ở `docs/`, portal source ở `src/redmine_mcp_docs`, bản Việt ở `vi/`. Sửa source, export/restart; không sửa generated output. Khi thêm bản dịch chi tiết, cập nhật registry `assets/language.js` để route local được ưu tiên. Browser assets/Python server độc lập MCP config; chỉ `src/redmine_mcp/` vào wheel/runtime image. Xem [bảo trì portal](documentation-portal.md).

## Dependency và packaging :id=dependencies-and-packaging

uv cập nhật metadata/resolution cùng nhau; review `pyproject.toml` và `uv.lock`, không hand-edit hash hoặc upgrade ngoài scope. Lock/build chỉ chạy trong assignment phù hợp. Unit/integration mặc định offline; live cần explicit E2E flag và môi trường owned pin. Coding-without-tests bàn giao dependency/fixture/execution riêng; ngưỡng coverage và testing CI hoãn. [Ledger lịch sử](testing/evidence/current-catalog-acceptance.md) không chứng nhận mọi trạng thái mới.

## Phụ lục ví dụ nguyên văn

Các đoạn mã/lệnh sau giữ nguyên từ bản gốc để tra cứu cú pháp. Không thực thi tự động; chỉ chạy bước kiểm thử hoặc mutation khi assignment cho phép.

```bash
bash scripts/doctor.sh
uv sync --frozen
bash scripts/check.sh
```

```bash
uv run --frozen uvicorn redmine_mcp.app:create_app --factory --host 127.0.0.1 --port 8000 --reload --no-access-log
```

```bash
uv run --frozen ruff check .
uv run --frozen ruff format --check .
uv run --frozen mypy src
uv run --frozen python scripts/check_architecture.py
```

```bash
uv run --frozen ruff format .
```

```bash
uv run --frozen pre-commit validate-config
uv run --frozen pre-commit install
uv run --frozen pre-commit run --all-files
```

```bash
uv run --frozen pre-commit uninstall
```

```python
from redmine_mcp.features import IssueService, ProjectService, ReferenceService, TimeEntryService
from redmine_mcp.features.issues import IssueService
from redmine_mcp.auth import AuthContext, AuthenticationService
from redmine_mcp.common import ApplicationError, Page
from redmine_mcp.integrations.redmine import RedmineClient, RedmineIssues
from redmine_mcp.mcp import register_mcp
```

```python
from redmine_mcp.common import InvalidInputError
from redmine_mcp.constants import issues as issues_text

raise InvalidInputError(issues_text.PROJECT_REQUIRED_FOR_CATEGORY)
```

```bash
bash scripts/docs-portal.sh export
bash scripts/docs-portal.sh serve
```

```bash
uv add --dev pre-commit
uv lock --check
uv build
```
