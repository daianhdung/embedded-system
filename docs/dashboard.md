# Dashboard local — giám sát, AI và lịch sử

## Chạy

Terminal tại firmware:

```sh
.venv/bin/python -m pip install -r tools/requirements-dashboard.txt
.venv/bin/python -m streamlit run dashboard/app.py --server.address 127.0.0.1 --server.headless true --browser.gatherUsageStats false
```

Mở http://127.0.0.1:8501. Hoặc VS Code → Terminal → Run Task → **PCCC: Dashboard**. Máy hiện tại đã cài thư viện.

Dashboard tự kết nối broker local theo `.env`. Host/port nằm trong mục thu gọn Cài đặt nâng cao; không nhập trên UI. Xem [khởi động local](local-setup.md).

Mở Wokwi và publisher ở terminal khác. Dashboard subscribe dữ liệu, không gửi lệnh điều khiển. Có thể đóng dashboard mà local ESP vẫn chạy.

## Đọc dashboard

- Header chỉ báo ESP cập nhật khi có telemetry mới trong15giây PC, đúng phiên collector, không retained/fixture và không nhận offline mới hơn. Kết nối broker không có nghĩa ESP đang online. Dữ liệu import/DB cũ không bao giờ tự thành live.
- Cảm biến: ADC khói/LDR, nhiệt/ẩm; null hiện dấu —. Các giá trị cuối vẫn hiện khi stale nhưng có nhãn lịch sử.
- Tải: lệnh bơm, van, cửa, còi/LED; đây không phải phản hồi tiếp điểm hoặc vị trí servo.
- AI: bản tin gửi tại broker, backend/model, trạng thái publisher và số ESP chấp nhận/từ chối là thông tin riêng. PUBACK không tự chứng minh ESP chấp nhận; AIlevel0 không tự là nhãn bìnhthường. Unknown/STOP/ERROR không được giả thành normal.
- Biểu đồ theo thời điểm PC nhận; không dùng timestamp Wokwi để đo latency thật.
- EVENT lưu SQLite, xem và tải CSV. Không bảo đảm thu đủ event nếu mất mạng; ESP phát QoS0.
- Nghiệm thu: xem bảng260lượt gốc, không có nút tự ghi PASS.

`ai_publish.py` nay phát thêm metadata khôngretained tại `<prefix>/ai/status` (START/PUBACK/UNAVAILABLE/CONFIRMING/STOP/ERROR, model/backend/publisher_id/clockdomain). Last-will OFFLINE và timeout giúp thấy nguồn AI mất. Topic điều khiển `ai/result` vẫn giữ4trường. Không gửi ảnh camera lên broker.

SQLite nằm tại `runs/dashboard.sqlite3`, mặc định giữ khoảng50.000bản ghi/prefix, dedup QoSduplicate, WAL. DB/log không commit. Khi nhiều người dùng chung cùng app, kết nối subscriber cache được chia sẻ; đây là dashboard local một nhóm, chưa có tài khoản/phân quyền đa người dùng.

## Xem lại capture đã lưu

```sh
.venv/bin/python tools/dashboard_import.py --capture runs/replay-clock-01.jsonl
```

Dữ liệu import luôn là lịch sử. Nó không tự kết nối MQTT và không ghi vào bảng nghiệm thu. Muốn xem lịch sử không kết nối, khởi động dashboard với PCCC_DASHBOARD_OFFLINE=1.

## Kiểm chứng

- Test store: stale/offline, DB từ phiên cũ, retained, dữ liệu lỗi, duplicate và sai firmware.
- Streamlit AppTest: trang render offline/history, không có nút ACK/bơm/cửa.
- Localhost broker smoke: telemetry fixture + status/AI từ publisher đến SQLite. Fixture không được hiện là ESP live.
- Cần nghiệm thu với Wokwi: thay cảm biến, xem state/event/tải, tắt nguồn ESP hoặc mạng, đóng dashboard và xác nhận local vẫn hoạt động.

Nguồn API: [Streamlit fragment](https://docs.streamlit.io/develop/api-reference/execution-flow/st.fragment), [cache resource](https://docs.streamlit.io/develop/api-reference/caching-and-state/st.cache_resource).

## Giao diện tra cứu mới · 29/10/2026

Luồng đọc: **Chọn thẻ cảm biến → biểu đồ tương ứng → chọn điểm hoặc ID → bản ghi nguồn**.

- Tổng quan ưu tiên trạng thái ESP, lý do ESP đang báo, broker kết nối và AI còn hiệu lực theo ESP. Khi offline, tất cả thẻ là snapshot cuối đã lưu, không có nhãn an toàn giả. Các thẻ không đổi theo bộ lọc lịch sử; ngay trên thẻ ghi rõ điều này.
- Bốn thẻ có màu riêng cố định: khói/gas nâu, LDR tím, nhiệt đỏ, ẩm xanh. Mỗi thẻ là nút Streamlit cao 138px ở desktop, hiển thị tên, giá trị và đơn vị; viền xanh đánh dấu cảm biến đang chọn. Trạng thái riêng hiện khi có dữ liệu trực tiếp; khi offline, dòng phụ là nguồn sensor/GPIO, còn trạng thái lịch sử nằm trong header chung. Chọn thẻ đồng bộ selectbox, chart và cột bảng, chuyển về tab tra cứu. Snapshot ID, timestamp và live/history chỉ hiện chung một lần; metadata đầy đủ trong mục thu gọn.
- Một biểu đồ lớn cho cảm biến đang chọn, tránh trộn đơn vị °C/%/ADC. Tooltip có giá trị chính xác, thời gian nhận đến ms, state ESP và record ID. Đường đứt lấy từ include/config.h hiện tại; tam giác chỉ những snapshot có cờ liên quan do ESP phát. Không tự hồi dựng FSM hoặc gán bình thường từ số đo.
- Bộ lọc **Lần chạy cuối / 15 phút / 1 giờ / 24 giờ / Tất cả đã lưu** áp dụng cho biểu đồ, bảng và tab EVENT. Lần chạy cuối theo boot_id; các khoảng tương đối theo giờ PC hiện tại. Lấy tối đa 2.000 snapshot và 500 EVENT mới nhất sau lọc, không lấy trung bình hay tự điền mẫu thiếu. Tổng quan vẫn là snapshot mới nhất toàn bộ DB.
- Chọn điểm trên biểu đồ mở đúng record_id, giữ ổn định qua các lần cập nhật. Bảng có lọc snapshot cảnh báo, CSV theo đúng bộ lọc và chọn ID để xem JSON/topic/firmware/boot/uptime gốc. ID thay cho chỉ số hàng giúp tránh trỏ sang bản ghi khác khi bảng cập nhật.
- Lệnh thiết bị vẫn tách khỏi feedback cơ khí. AI phân biệt kết quả tại broker với xử lý của ESP; metadata và cấu hình kỹ thuật được thu gọn. Nghiệm thu vẫn chỉ đọc.

### Giới hạn dữ liệu và kiểm chứng

MQTT hiện không có timestamp đo hay cờ chất lượng riêng từng cảm biến; dashboard chỉ biết giá trị trong snapshot và thời điểm PC nhận. Chưa được suy tuổi mẫu DHT từ tuổi bản tin. Ngưỡng config.h hiện tại có thể khác firmware cũ trong DB; giải thích hysteresis và điều này nằm ngay dưới biểu đồ. Không có telemetry thì không tự dựng dữ liệu hay tạo điểm an toàn.

Altair đã đi kèm Streamlit được tái sử dụng, không thêm thư viện. Phần trình bày nằm ở `dashboard/presentation.py`, biểu đồ ở `dashboard/charts.py`, truy vấn lịch sử có lọc ở `Store.window`. Collector/MQTT, firmware và phép tính điều khiển giữ nguyên.

Kiểm thử gồm UI rỗng và DB fixture tách biệt; đối chiếu KPI = endpoint chart = giá trị gốc cả bốn cảm biến; điều hướng metric, time filter, chọn ID; các test stale/retained/offline và smoke MQTT→SQLite. Kiểm tra trình duyệt ở desktop và màn hình nhỏ trên dữ liệu đã lưu thực tế. Fixture kiểm thử không được đưa vào DB dashboard của người dùng.

### Tinh gọn bố cục · 29/10/2026

Bỏ nút “Xem xu hướng” và panel lệnh thiết bị lớn. Sáu badge bơm/van/cửa/còi/đèn đỏ/đèn xanh tự xuống dòng khi màn hình nhỏ; chú thích lệnh đã ghi nhận, chưa có phản hồi vật lý luôn hiện ngay dưới. Khoảng lọc không thay KPI mới nhất. Chọn ID để xem JSON theo đúng cảm biến/khoảng đang tra; khóa chọn bản ghi tách theo sensor để tránh kéo lựa chọn cũ sang sensor khác. Không sửa Store, collector, dữ liệu lịch sử, phép tính, thresholds hay firmware.

### Thẻ đồng hồ bán nguyệt theo mẫu · 29/10/2026

Bốn thẻ nay là gauge SVG trong native Streamlit button: tên, cung bán nguyệt, số đọc chính xác/đơn vị ở giữa, hai đầu thang và dòng trạng thái/nguồn. Toàn bộ thẻ vẫn chọn được, đồng bộ chart/filter/raw table như trước. Cao 160px desktop. Không có JavaScript hoặc thư viện mới.

MQ-2/LDR hiển thị thang ADC0–4095; độ ẩm0–100%; nhiệt độ mặc định0–100°C là **thang hiển thị**, không phải ngưỡng an toàn hoặc cam kết dải đo cảm biến. Thang nhiệt tự mở rộng nếu số đọc ngoài khoảng, số đọc không bị cắt hay sửa. Cung thể hiện vị trí số đo trong thang, không phải phần trăm nguy cơ cháy. LDR sáng tăng thì ADC giảm như trước. Ngưỡng/cờ cảnh báo vẫn lấy từ logic hiện có và biểu đồ. Khi offline, màu cung nhạt hơn và header tiếp tục ghi lịch sử; khi thiếu mẫu, hiện “—”, không hiện số0 thay thế.
