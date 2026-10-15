# Lộ trình kiểm thử

### Hoàn tất bổ sung ca kiểm thử cho danh mục MCP (2026-10-13)

Các ca có thể thực thi mới và [danh mục truy vết 36 công cụ](testing/mcp-catalog-cases.md)
bao phủ xác thực danh mục, kiểm tra hợp lệ và các cổng ghi, cùng với việc tạo mục thời gian,
khám phá hoạt động dự án và tag trong chi tiết issue. Các ca tạo/hoạt động gốc chỉ chạy khi được
bật sử dụng fixture dự án thời gian đã có biện pháp bảo vệ, cùng một vai trò/người dùng chỉ đọc
do dự án này quản lý. Nhiệm vụ này chỉ tạo các ca kiểm thử; không chạy kiểm thử, gọi Inspector
hay thực hiện thay đổi trực tiếp nào. Sau đó, người dùng báo có sáu lỗi khi tạo. Assertion đọc
lại hiện bỏ qua các yêu cầu GET khám phá của SDK, còn đăng ký công cụ cấm các đối số tạo thừa.
Các sửa đổi này đang chờ chạy lại; việc nghiệm thu và những thiếu sót trước đó về chính sách
gốc/plugin theo từng nhiệm vụ vẫn đang chờ xử lý.

### Nghiệm thu xóa mục thời gian của issue

Người dùng giao riêng việc kiểm thử TOOL-043 vào ngày 2026-10-08. [Bằng chứng xóa](testing/evidence/tool-043-testing.md)
ghi nhận 32 ca unit trong `tests/unit/test_time_entry_deletions.py`, 82 ca integration chuyên biệt
trong `tests/integration/test_time_entry_deletions.py`, bốn ca bổ sung cho ma trận writer hiện tại,
và 1889 lượt kiểm thử hồi quy ngoại tuyến sạch hoàn toàn. Kiểm thử phát hiện và sửa lỗi bỏ qua
các đối số MCP chưa khai báo; thao tác xóa hiện từ chối rõ ràng các đối số đó. Nghiệm thu gốc trong
`tests/e2e/test_time_entry_delete_acceptance.py` đã chạy đạt 11 ca cùng một ca bổ sung về quyền khi
không xem được issue, bao gồm Inspector 2.8.0. Việc thiếu dữ liệu trong vùng lưu trữ do dự án sở hữu,
các kiểm soát và tổng số, ranh giới vai trò, biên nhận cho lệnh gọi trùng/lệnh gọi độc lập, lỗi đã
được ghi nhận và tình huống race khi mục bị di chuyển đều có bằng chứng đạt. Báo cáo dọn dẹp chính
xác xác nhận không còn dự án/mục/người dùng/vai trò/hoạt động nào; cũng không còn sổ theo dõi tác vụ
riêng tư hay cấu hình Inspector. Các kiểm tra trong phạm vi đã đạt; giới hạn về injection/chính
sách/plugin vẫn được công bố. Không khẳng định đã chạy lại cuối cùng cả 12 ca gốc trong một lần.
Việc tạo TOOL-041 vẫn là nhiệm vụ riêng.

Người dùng giao kiểm thử TOOL-042 vào ngày 2026-10-08.
[Bằng chứng cập nhật mục thời gian](testing/evidence/tool-042-testing.md) ghi nhận 61 ca unit/99 ca
integration chuyên biệt, cập nhật fixture danh mục dùng chung, 10 ca Redmine 7.0.2/Inspector do
dự án sở hữu và xác nhận dọn dẹp không còn tài nguyên nào. Kiểm thử hồi quy ngoại tuyến toàn bộ có
1.755 ca đạt và một lỗi đối số reader cũ; lượt chạy lại sau khi sửa lỗi cùng bảy ca tình huống biên
về sau đều đạt. Tài liệu không khẳng định đã chạy lại sạch toàn bộ bộ kiểm thử sau các bổ sung/sửa
nhỏ cuối cùng. Kiểm thử dùng thiết lập gốc hiện tại mà không thay đổi vai trò dùng chung, thiết lập
toàn cục, plugin hay máy chủ 6.0.5 dùng chung. Các biến thể rộng hơn về chính sách/plugin/race và
các khoản nợ Ruff không liên quan của kho mã vẫn được công bố.

Người dùng cho phép kiểm thử cho prep-022 đến prep-026 vào ngày 2026-10-07.
[Kiểm thử hồi quy khâu chuẩn bị](testing/evidence/prep-022-026-testing.md) ghi lại các kiểm thử mới,
lỗi runtime và cách sửa, kết quả live/Inspector thuộc dự án, việc dọn dẹp và bằng chứng ngoại tuyến cuối cùng.

Sau đó, người dùng giao kiểm thử PREP-027 vào ngày 2026-10-07.
[Xác minh thử lại thao tác đọc](testing/evidence/prep-027-testing.md) ghi nhận các tình huống thử lại
xác định được, ngân sách/hạn chót, hủy, danh tính, biên nhận REST/MCP và writer, hợp đồng lỗi reader
đã điều chỉnh, cùng khả năng tương thích live/Inspector chỉ đọc thuộc dự án. Việc đưa lỗi vào và
các thay đổi dữ liệu được kiểm thử ngoại tuyến; các kiểm tra live được chọn không tạo thay đổi nào.

Việc xác minh hiện có ba lớp: kiểm thử unit, kiểm thử integration REST/MCP ngoại tuyến và E2E live
chỉ chạy khi được cho phép trên môi trường Redmine có phiên bản do dự án sở hữu lựa chọn. CI kiểm
thử và ngưỡng phần trăm độ phủ vẫn được hoãn. [Ma trận độ phủ](plans/testing-coverage.md) ánh xạ
mỗi thao tác hiện tại và tình huống runtime phổ biến vào nhiệm vụ cùng bằng chứng được chọn.

Ngày 2026-10-07, [PREP-020](plans/tasks/prep-020-current-catalog-acceptance.md) đối chiếu danh mục
chức năng 32 thao tác: **1.086 kiểm thử ngoại tuyến và 21 kiểm thử live Redmine 7.0.2 do dự án sở
hữu đã đạt**. [Sổ ghi PREP-020](testing/evidence/current-catalog-acceptance.md) ghi lại revision nguồn
và bằng chứng chính xác, bao gồm các phiên bản, thành viên, `allowed_all`, tình huống không chắc chắn
khi ghi dùng chung và khả năng tương thích danh mục/đọc của Inspector. Các biến thể lịch sử rộng hơn
vẫn nằm trong H1..H6; số lượng kiểm thử không tự động khép lại các mục đó. Không chạy lại kiểm thử
hay kiểm tra runtime nào cho cập nhật tài liệu PREP-021. Danh mục đã đăng ký hiện có 18 thao tác đọc
và 18 thao tác ghi; xem [tóm tắt lộ trình hiện tại](plans/index.md#catalog-status-2026-10-09) để biết
bằng chứng về sau và các giai đoạn nghiệm thu còn chờ hoặc được miễn. Số lượng kiểm thử không tự động
khép lại các khoảng trống đó.

## Triển khai theo ba giai đoạn

| Giai đoạn | Thư mục | Nhiệm vụ | Môi trường |
|---|---|---|---|
| Unit | `tests/unit/` | [prep-016](plans/tasks/prep-016-unit-testing.md) | Cổng giả lập, model và chính sách |
| Integration | `tests/integration/` | [prep-017](plans/tasks/prep-017-offline-integration-testing.md) | Redmine giả lập và REST/MCP chạy trong tiến trình |
| E2E | `tests/e2e/` | [prep-018](plans/tasks/prep-018-live-e2e-testing.md) | Redmine 6.x.x hoặc 7.0.2 được chọn, do dự án sở hữu, và PostgreSQL |

Người dùng đã cho phép triển khai và thực thi vào ngày 2026-10-05. Các nhiệm vụ chỉ lập trình trong
tương lai vẫn cần được cho phép kiểm thử riêng. Chạy từ Git Bash trong phạm vi nhiệm vụ đã được phép:

```bash
uv run --frozen pytest tests/unit
uv run --frozen pytest tests/integration
uv run --frozen pytest
bash scripts/check.sh
```

Khám phá mặc định chỉ chọn unit và integration. Chọn E2E tường minh mà thiếu `--run-e2e` sẽ kết thúc
với lỗi cách dùng trước khi fixture chạy. Fixture ngoại tuyến tắt việc nạp dotenv, xóa thiết lập
Redmine được kế thừa và từ chối gửi mạng HTTPX thực. Trợ giúp về dữ liệu dùng chung và phiên MCP nằm
trong `tests/helpers.py`; các module kiểm thử được thu thập không cung cấp helper cho module khác.

### Các stack tổng hợp có phiên bản

E2E dùng các stack Compose có phiên bản hiện có. Khâu chuẩn bị chỉ khởi động dịch vụ `postgres` và
`redmine` của chúng, sau đó tạo dữ liệu fixture mà pytest cần. Khâu này không tạo thêm dự án
`redmine-mcp-e2e*`, không build image ứng dụng MCP và không cần các bộ dữ liệu demo/history lớn.
Kiểm thử chạy ứng dụng MCP trong tiến trình bằng khóa người dùng cá nhân.

| Redmine | Dự án Compose | Redmine trên máy chủ | PostgreSQL trên máy chủ | Reader / writer tùy chọn | Trạng thái E2E riêng tư |
|---|---|---|---|---|---|
| 6.0.1 | `redmine-mcp-dev-6-0-1` | `127.0.0.1:3001` | `127.0.0.1:5436` | 8001 / 8003 | `.local/e2e/redmine-mcp-dev-6-0-1/` |
| 7.0.2 | `redmine-mcp-dev-7-0-2` | `127.0.0.1:3002` | `127.0.0.1:5433` | 8002 / 8004 | `.local/e2e/redmine-mcp-dev-7-0-2/` |

Cả hai container Redmine đều lắng nghe cổng 3000 bên trong. Dùng Docker Compose 2.24.4 trở lên.
Chạy từ thư mục gốc kho mã bằng Git Bash, khi Docker Desktop đang chạy và `uv` có trong `PATH`.
Bộ kiểm thử cần Node.js/npm cho các ca Inspector; lần gọi Inspector đầu tiên có thể tải gói đã ghim
phiên bản. Cài các dependency Python đã khóa bằng `uv sync --frozen`. Có thể chạy E2E trực tiếp trên
bản checkout mới mà không cần chạy `dev-up.sh` trước.

### Chọn bản Redmine

Chạy lần lượt hai bộ kiểm thử. Xóa các biến ghi đè cổng/image đã export trước đó để dùng giá trị mặc định:

```bash
unset REDMINE_E2E_COMPOSE_FILE REDMINE_E2E_COMPOSE_PROJECT REDMINE_E2E_ENV_FILE
unset REDMINE_E2E_PORT REDMINE_E2E_IMAGE
REDMINE_E2E_VERSION=6.0.1 uv run --frozen pytest tests/e2e --run-e2e
REDMINE_E2E_VERSION=7.0.2 uv run --frozen pytest tests/e2e --run-e2e
```

Pytest tự chạy `uv run --frozen python scripts/prepare-e2e.py` một lần cho mỗi phiên trước khi
fixture live và kiểm thử bắt đầu. Khâu chuẩn bị chọn profile Compose hiện có, xác thực image pin,
dấu tổng hợp và volume, áp dụng các mount hiện tại, chờ dịch vụ khỏe mạnh, rồi tạo sáu người dùng
E2E có tên cùng dữ liệu vai trò/dự án/issue/báo cáo. Những lần chuẩn bị lặp lại xác minh và tái sử
dụng fixture thuộc dự án. Các khác biệt vai trò người dùng cần cho kiểm thử quyền được giữ nguyên.
Nếu khâu chuẩn bị lỗi, phiên dừng trước khi chạy kiểm thử.

`REDMINE_E2E_VERSION` chọn pytest và các công cụ bổ sung. `REDMINE_TEST_VERSION` chọn helper vòng đời
phát triển; trình khởi chạy E2E tự đặt biến này theo phiên bản E2E. Stack 6.0.1 đang chạy không
chuyển kiểm thử 7.0.2 sang cổng 3001: lệnh đó chọn dự án phát triển 7.0.2 riêng trên cổng 3002.

Để chạy tập trung, giữ phiên bản và cờ bật tường minh:

```bash
REDMINE_E2E_VERSION=7.0.2 uv run --frozen pytest tests/e2e/test_reporting_acceptance.py --run-e2e -q
```

Lệnh này cũng chuẩn bị một lần trước các ca live đã chọn. Lượt chạy thành công giữ lại fixture nền
để dùng lại và dọn dẹp các tài nguyên kiểm thử dùng một lần.

Chạy ngoại tuyến, `--collect-only` và chạy khi không có kiểm thử E2E nào được chọn sẽ không chuẩn bị
Docker. Chọn E2E mà không có `--run-e2e` vẫn lỗi trước bước thiết lập. Có thể chạy riêng lệnh chuẩn bị
trước các kiểm tra bổ sung:

```bash
REDMINE_E2E_VERSION=6.0.1 uv run --frozen python scripts/prepare-e2e.py
REDMINE_E2E_VERSION=6.0.1 uv run --frozen python scripts/verify-e2e-supplement.py
```

Đặt cùng phiên bản/profile cho khâu chuẩn bị, pytest và script bổ sung. Các stack Docker có thể
cùng tồn tại, nhưng hãy chạy tuần tự từng bộ vì listener ứng dụng bổ sung vẫn dùng chung các cổng
tạm thời. Mặc định chọn 7.0.2. Cấu hình chấp nhận bản phát hành ổn định chính xác 6.x.x và 7.0.2;
các bản 7.x khác, tag trôi, bản phát hành trước và phiên bản chính lớn cũ hơn đều bị từ chối. Chỉ
6.0.1 và 7.0.2 có profile dựng sẵn. Các bản 6.x khác cần đủ bốn thiết lập:

| Thiết lập | Giá trị profile tùy chỉnh bắt buộc |
|---|---|
| `REDMINE_E2E_COMPOSE_FILE` | Ghi đè cục bộ trong kho mã hiện có, kết hợp với `deploy/compose.yaml` |
| `REDMINE_E2E_COMPOSE_PROJECT` | Tên dự án Compose tường minh |
| `REDMINE_E2E_ENV_FILE` | Tệp env tổng hợp trong `.local/` bị Git bỏ qua hoặc `.env` tại thư mục gốc |
| `REDMINE_E2E_PORT` | Cổng máy chủ 1024..65535, khớp ánh xạ localhost tới cổng 3000 của profile |

Profile tùy chỉnh phải bao gồm dấu nhận diện/dự án E2E, mount chỉ đọc `/opt/testing`, mount ghi được
`/e2e-state`, cùng các volume `redmine_db_data`/`redmine_files` thuộc dự án và được gắn nhãn theo
môi trường tổng hợp lẫn phiên bản chính xác. Profile dựng sẵn không cần tệp env. Chúng dùng tệp
Compose độc lập theo phiên bản và thêm `deploy/compose.e2e.yaml` để chuẩn bị E2E cùng các lệnh gọi
helper gốc mount bằng chứng trên máy chủ tại `.local/e2e/<project>/`. `dev-up.sh` dùng volume có tên
và không tạo thư mục cấu hình hay bằng chứng trên máy chủ. Khâu chuẩn bị tự cung cấp
`REDMINE_E2E_STATE`; người dùng không đặt biến này cho profile dựng sẵn. Image chính thức phải có
dạng `redmine:<version>[-variant]@sha256:<64-hex-digest>`. `REDMINE_E2E_IMAGE` là tùy chọn phải
khớp pin đã cấu hình; biến này không thay thế image. Không có phương án dự phòng sang bản phát hành
khác hoặc stack độc lập được sinh tự động.

### Đặt lại và di chuyển

Khâu chuẩn bị pytest thông thường không đặt lại cơ sở dữ liệu. Để chủ động bắt đầu mới trên stack
tổng hợp dùng một lần đã chọn, dùng cờ reset độc lập:

```bash
REDMINE_E2E_VERSION=6.0.1 uv run --frozen python scripts/prepare-e2e.py --reset
REDMINE_E2E_VERSION=7.0.2 uv run --frozen python scripts/prepare-e2e.py --reset
```

Mỗi lệnh dừng/xóa container của dự án đã chọn, chỉ xóa volume cơ sở dữ liệu/tệp đã kiểm tra và có
dấu nhận diện, xóa thư mục trạng thái E2E trên máy chủ đã chọn, rồi chuẩn bị fixture mới. Các dự án
khác, thông tin xác thực env và trạng thái của phiên bản kia được giữ lại. Khâu chuẩn bị chỉ khởi
động lại PostgreSQL/Redmine; có thể khởi động riêng các dịch vụ MCP Docker tùy chọn. Reset từ chối
tài nguyên/volume không thuộc dự án hoặc không có dấu nhận diện, và volume đang được dự án khác dùng.

Các dự án và volume cũ `redmine-mcp-test*` được để nguyên. Dự án dựng sẵn mới dùng volume độc lập
và thông tin xác thực cục bộ cố định. Dừng container cũ nếu chúng chiếm cổng cần thiết. Manifest
demo/history được giữ riêng và sẽ cũ sau khi reset cơ sở dữ liệu: hãy dùng quy trình tái khởi tạo
có bảo vệ của chúng trước khi chạy lại trình sinh dữ liệu. E2E reset giữ volume `seed_state` của
môi trường phát triển, vì vậy manifest không tự trở nên hợp lệ chỉ nhờ chạy lại `dev-up.sh`. Thay
vào đó, để tạo môi trường demo/history mới, hãy dùng riêng [reset môi trường phát triển](operations.md#seed-and-reset).
Lệnh reset đó cũng làm mất hiệu lực mọi manifest E2E còn trên máy chủ; hãy reset E2E tường minh
trước khi quay lại kiểm thử live.

Các stack E2E độc lập cũ và tệp `.local/testing-e2e*/` không được tự động di chuyển hoặc xóa. Không
được sao chép ID cơ sở dữ liệu của chúng vào manifest mới. Nếu stack cũ chiếm cổng cần thiết, trước
tiên hãy dừng đúng stack đã xác định.

Manifest và log E2E dựng sẵn nằm trong `.local/e2e/<project>/`, được mount tại `/e2e-state`. Profile
tùy chỉnh giữ dữ liệu ở `.local/e2e/<version>/`. Bằng chứng cũ được giữ nguyên. Trạng thái seed phát
triển giữ mount `/seed-state`. Nếu thiếu manifest nhưng tên fixture E2E bị trùng, hoặc còn
`setup.json` từ lần thiết lập bị gián đoạn, cần reset tường minh; khâu chuẩn bị không bao giờ nhận
quyền sở hữu bản ghi chỉ dựa trên tên khớp.

Chẩn đoán là riêng tư: `pytest-prepare.log` chứa đầu ra khâu chuẩn bị, `compose-up.log` chứa đầu ra
khởi động dịch vụ, còn `seed.log` chứa đầu ra fixture gốc. Lệnh fixture TOOL-042/043 cũng ghi
`tool042-<action>.log` và `tool043-<action>.log` trong thư mục trạng thái riêng đã chọn, bao gồm
thông tin chẩn đoán khi thiết lập lỗi. Các log này có thể chứa khóa cá nhân. Không bao giờ dán thông
tin xác thực hay log chưa được che vào bằng chứng dùng chung. Kiểm tra trước khi chạy xác minh dịch
vụ/image/cổng/mount đang chọn, phiên bản Redmine gốc, nhãn volume và quyền sở hữu manifest/tài nguyên
trước khi thay đổi dữ liệu kiểm thử. Ứng dụng MCP vẫn không truy cập trực tiếp cơ sở dữ liệu.

Khâu chuẩn bị sửa quyền danh mục và trạng thái active/closed/archived mong đợi chỉ cho fixture nền
do manifest sở hữu. Vị trí cây dự án được tải lại trước khi đổi trạng thái; việc đối soát quyền còn
thiếu hoặc có hậu duệ ngoài dự kiến sẽ làm dừng thiết lập. Phản hồi dự án Redmine 6.0.1 bỏ qua phân
trang chỉ được cắt cục bộ khi chứa toàn bộ bộ sưu tập đã đếm, có ID khác nhau hợp lệ và phần phản
hồi phân trang khớp. Các dạng phản hồi khác vẫn cần xác thực trang nghiêm ngặt. Chính sách fixture
mục thời gian dùng thiết lập đã cài; nếu thiếu thiết lập ghi log thời gian trên issue đã đóng thì
đó là hành vi gốc không hạn chế của 6.0.1.

Adapter chuyển các chuỗi giờ hữu tỉ gốc như `"5/4"` từ Redmine 6.0.1 thành số giờ. Đầu vào ghi công
khai vẫn yêu cầu số JSON. Xác minh biên nhận tính đến bộ lấy giá trị theo phút nguyên của Redmine
gốc và cách biểu diễn hai chữ số thập phân ở các bản mới hơn. Khâu chuẩn bị cũng gắn tag
`notification` lên issue nền thuộc dự án, giúp các kiểm soát tag dương tính và âm tính chỉ đọc chạy
với plugin tag đã cài sẵn thay vì bị bỏ qua do thiếu dữ liệu dương tính.

Các stack Compose giữ lại plugin đã khai báo. Tình huống tag cần lọc tag gốc hoạt động và fixture
tag dương tính hiện có; thiếu điều kiện tiên quyết sẽ được bỏ qua tường minh. Bỏ qua không đồng nghĩa
với nghiệm thu tính tương thích. Nghiệm thu thiết lập hiện tại cần bằng chứng thực thi có ghi ngày.
[Bằng chứng 6.0.1 có ngày](testing/evidence/prep-029-redmine-6.0.1.md) ghi nhận 50 ca đạt trên thiết lập
`redmine-mcp-test-6-0-1` trước đây. Bằng chứng này không xác lập nghiệm thu cho đợt tái cấu trúc
`redmine-mcp-dev-*` tự chứa về sau. Việc nghiệm thu thiết lập hiện tại, 7.0.2, khả năng chạy đồng
thời và reset vẫn được theo dõi trong [nhiệm vụ](plans/tasks/prep-029-reuse-versioned-compose-e2e.md).

Assertion phân biệt giữa chấp nhận thao tác ghi và trạng thái khớp, bao gồm trường được chấp nhận
nhưng bị bỏ qua do giới hạn author/tracker. Kết quả không chắc chắn cần được đối soát trước khi thử
lại. Dọn dẹp chỉ tác động đến tài nguyên đã tạo; khôi phục tiêu đề fixture hoặc quyền vai trò có thể
để lại lịch sử journal do dự án sở hữu. Fixture nền và container vẫn sẵn sàng để chạy lại; không tự
động reset.

Script bổ sung khởi chạy ứng dụng localhost tạm thời ở cổng 18081, chạy khám phá Inspector 2.8.0 và
một lệnh đọc, sau đó dùng Edge/Node đã cài để tải attachment qua liên kết metadata đã xác thực và so
sánh nội dung. Script dừng ứng dụng/trình duyệt và xóa attachment đã tạo. Cấu hình thông tin xác
thực JSON, hồ sơ trình duyệt và kết quả đã che được giữ trong vùng bị bỏ qua. Để xem xét bổ sung
tương tác:

```bash
REDMINE_E2E_VERSION=6.0.1 uv run --frozen uvicorn tests.e2e.server:create_app \
  --factory --host 127.0.0.1 --port 18081
npx @modelcontextprotocol/inspector@2.8.0
```

Kết nối riêng tư tới `http://127.0.0.1:18081/mcp` bằng khóa của người dùng thông thường thuộc dự án.
Ví dụ này dùng 6.0.1; dùng `REDMINE_E2E_VERSION=7.0.2` cho đích 7.0.2 đã chuẩn bị. Dùng URL Redmine
của profile đã chọn (3001 cho 6.0.1, 3002 cho 7.0.2); không đưa khóa vào URL hay ảnh chụp màn hình.

### Khắc phục sự cố khâu chuẩn bị

Nếu pytest thoát với `E2E preparation failed` trước khi chạy ca nào, trước tiên hãy đọc log chuẩn bị
riêng của dự án đã chọn. Các tệp log về sau có thể chưa tồn tại nếu thiết lập lỗi sớm:

```bash
cat .local/e2e/redmine-mcp-dev-7-0-2/pytest-prepare.log
```

Với 6.0.1, thay bằng `redmine-mcp-dev-6-0-1`. Kiểm tra `compose-up.log` để xem dịch vụ khởi động,
`seed.log` để xem thiết lập fixture gốc, và `tool042-<action>.log` hoặc `tool043-<action>.log` để
điều tra lỗi fixture theo nhiệm vụ. Đây là lệnh chẩn đoán cục bộ; không chia sẻ log chưa được che.

| Triệu chứng | Cách xử lý |
|---|---|
| Thiếu `uv`, Docker hoặc Compose không được hỗ trợ | Cài công cụ cần thiết, khởi động Docker Desktop và chạy lại từ thư mục gốc kho mã. |
| Cổng đã bị chiếm | Xác định và dừng dịch vụ xung đột được báo cáo; khâu chuẩn bị không dừng dự án khác. |
| `Selected env file is not marked as synthetic` | Trường hợp này áp dụng cho profile dùng tệp env tùy chỉnh hoặc mã thiết lập cũ. Profile dựng sẵn không dùng tệp env: xóa các ghi đè E2E tùy chỉnh như trên và kiểm tra checkout có trình khởi chạy hiện tại. Không đánh dấu `.env` bên ngoài là tổng hợp. |
| Volume, image, dự án hoặc phiên bản gốc không khớp | Sửa profile đã chọn và giữ các biện pháp bảo vệ quyền sở hữu. Đổi phiên bản dùng một lần được hỗ trợ cần reset tường minh. |
| Thiếu manifest nhưng có tên fixture E2E hiện hữu, hoặc sổ thiết lập chưa hoàn chỉnh | Đối soát trạng thái thuộc dự án hoặc dùng reset stack đã chọn tường minh khi có thể xóa dữ liệu. |
| Lệnh Inspector lỗi | Kiểm tra Node.js/npm và bằng chứng Inspector riêng; giữ nguyên phiên bản đã ghim. |
| Chỉ có cảnh báo `PydanticDeprecatedSince211` | Dependency FastAPI-MCP đã ghim dùng hook schema Pydantic cũ hơn. Cảnh báo không liên quan lỗi chuẩn bị; hãy kiểm tra kết quả hoặc thông báo thoát của pytest. |

Sau khi `dev-up.sh` hoặc thao tác khác tạo lại Redmine mà không có overlay E2E, hãy chạy chuẩn bị
lại trước các script Inspector/trình duyệt độc lập. Pytest tự làm bước này. Xóa tệp cache Python hay
script helper bị Git bỏ qua không reset dữ liệu Docker. Xóa manifest E2E đang hoạt động không chứng
minh quyền sở hữu các bản ghi còn trong cơ sở dữ liệu.

## Lịch sử nền tảng và công việc tiếp theo

[Quy trình công cụ](workflows/redmine-tools.md) yêu cầu có nền tảng tự động ngoại tuyến trước khi
triển khai công cụ reader phụ thuộc. Nền tảng dùng dependency pytest và pytest-asyncio đã khóa, thiết
lập giả lập không có `.env`, HTTPX mock/ASGI transport và kiểm tra phiên MCP SDK. Chạy từ Git Bash,
không cần Docker hay thông tin xác thực:

```bash
uv run --frozen pytest
```

Bộ kiểm thử lịch sử bao phủ mười một công cụ reader thời điểm đó tại ranh giới REST và khám phá,
gọi công cụ, xác thực, kiểm tra hợp lệ cùng các gói lỗi MCP. Công việc prep-004 được cho phép cũng
bao phủ danh tính đồng thời, giới hạn số lần đọc upstream, readiness và dọn dẹp tài nguyên. Xem
[bằng chứng nghiệm thu có ngày](testing/evidence/prep-004-verification.md) để biết kết quả thực tế và
các khoảng trống fixture live còn lại. Kiểm tra tổng hợp live chỉ bật theo lựa chọn vẫn tách riêng;
ngưỡng độ phủ và CI kiểm thử cũng là các quyết định riêng.

Việc xác minh ghi hiện tại dùng writer tổng hợp bị giới hạn riêng, tài nguyên dùng một lần thuộc
nhiệm vụ, kiểm tra trạng thái sau thao tác và dọn dẹp cô lập. Thông tin xác thực reader hiện có phải
giữ quyền chỉ đọc. Xem [bảng điều khiển công cụ MCP](plans/index.md) để tra cứu phụ thuộc và tình
huống.

Backlog cũ bên dưới xác định các khu vực có thể tăng độ phủ, chứ không tuyên bố mọi tình huống đều
chưa được kiểm thử. Trước khi giao một khoảng trống, hãy tham khảo sổ hiện tại và nhiệm vụ gốc của
người phụ trách:

- Unit: bộ lọc/dự phòng/phân trang của service với gateway giả lập.
- Integration: ánh xạ, lỗi upstream, TLS/timeout, xác thực bằng khóa cá nhân và chuyển tiếp.
- MCP: schema/tên, phản hồi lỗi, tắt ứng dụng và dọn dẹp phiên.
- E2E: dự án giới hạn quyền/issue riêng tư/journal riêng tư, bộ lọc và phân trang.
- Seed: chạy lại, ghi bị gián đoạn, số lượng mong đợi và ranh giới truy cập.
- Backup/restore: volume mới, ID/lịch sử/quyền, checksum attachment, snapshot không tương thích/không đầy đủ và khôi phục lỗi.
- Đóng gói: wheel cô lập, image không chạy bằng root, ranh giới import và CI.

Các lệnh gọi cơ bản thành công không chứng minh hệ thống sẵn sàng cho production.
Readiness vận hành, audit/metrics, CI/đóng gói và nghiệm thu khôi phục do dự án sở hữu vẫn bị hoãn
ngoài lộ trình phát triển cục bộ hiện tại; đánh giá phát hành cuối cùng vẫn là prep-009.

## Tình huống xác thực theo từng người dùng cho giai đoạn kiểm thử được cho phép riêng

Với các nhiệm vụ chỉ lập trình trong tương lai, không tạo hay chạy kiểm thử nếu chưa được cho phép
kiểm thử. Nhiệm vụ ba giai đoạn ở trên cho phép rõ việc xác minh hiện tại. Các tình huống bàn giao
xác thực ban đầu này vẫn hữu ích làm yêu cầu truy vết:

- Hai khóa riêng biệt ánh xạ tới hai ID người dùng Redmine khác nhau. Các lệnh gọi xen kẽ và đồng
  thời chỉ chuyển tiếp từng khóa tới `/users/current.json` và yêu cầu tài nguyên riêng của khóa đó;
  `me` vẫn được chuyển tiếp lên upstream.
- Khóa thiếu, trống, trùng hoặc bị từ chối đều trả về 401 trước khi có yêu cầu tài nguyên. Kết nối
  MCP và khám phá công cụ từ chối khóa không hợp lệ. Không khóa nào xuất hiện trong đối số công cụ
  hay lỗi.
- Phản hồi current-user sai định dạng, timeout, lỗi transport và thu hồi khóa về sau lần lượt tạo
  phản hồi đã làm sạch 502, 504, 502 và 401.
- Phạm vi hiển thị là `requesting_redmine_user`; ID thao tác, đầu vào, phân trang và wrapper phản hồi
  hiện có vẫn ổn định. Cổng ghi vẫn đóng ở các triển khai reader.
