# Sửa TIMESTAMP khi Wokwi chạy chậm hơn máy tính

Lượt người dùng ngày 28/10/2026 có MQTT/Sub/UTC=1/1/1/1, nhưng ESP từ chối replay với TIMESTAMP. Capture cho thấy 118 giây trên PC tương ứng khoảng32giây ESP. Vì vậy, UTC=1 (epoch đã có giá trị) không đảm bảo đồng hồ mô phỏng còn khớp PC. Capture cũ cũng đã kết thúc trước khi replay bắt đầu.

## Cách sửa đã triển khai

Thêm `--wokwi-clock` cho `tools/ai_publish.py`. Đây là **chuyển miền thời gian dành riêng cho mô phỏng**, không phải đồng bộ lại NTP hoặc UTC phần cứng.

Publisher subscribe telemetry của ESP, đợi mẫu mới có đúng firmware identity/boot và mạng/clock hợp lệ. Trước khi đọc ảnh hoặc tạo mẫu replay, nó giữ một mốc `ts_ms` từ telemetry. Kết quả gửi dùng mốc đó thay UTC máy tính; timestamp ảnh gốc, tuổi ảnh và tuổi telemetry vẫn lưu trong log Python dưới `clock_mapping`. Không cộng thời gian PC vào đồng hồ ESP vì hai đồng hồ đang tiến với tốc độ khác nhau.

Các ràng buộc:

- Chỉ bật khi người dùng truyền `--wokwi-clock` và `--expected-firmware-id`; mặc định vẫn UTC thật.
- Telemetry phải không retained, record TELEMETRY, mode SIMULATION, đúng firmware_id và có boot_id; WiFi/MQTT/Sub/clock đều true.
- Mẫu telemetry không quá5giây PC; đợi mẫu mới tối đa10giây. Một mốc không được dùng để làm mới AI nhiều lần. Thiếu mẫu thì không gửi; có thể bỏ lượt suy luận khi mốc đã cũ.
- Ảnh/kết quả quá15giây PC hoặc clock PC nhảy tương lai quá2giây không được gửi. Mốc telemetry được lấy trước khi đọc frame để không đóng dấu mới cho ảnh cũ.
- Mất kết nối vô hiệu mốc; boot_id thay đổi thì dừng publisher, yêu cầu chạy lại để tránh trộn phiên.
- Không đổi schema4trường, confidence, parser, chống replay, TTL15giây, future tolerance2giây, GPIO hoặc FSM trên ESP.

**TTL và các mốc điều khiển trên ESP vẫn tính bằng giây mô phỏng.** Không dùng chế độ này cho phần cứng thật hoặc số đo độ trễ vật lý. Nó cũng không sửa vấn đề Wokwi chạy chậm. Khi mô phỏng quá chậm, telemetry có thể quá5giây và publisher sẽ từ chối gửi; không tự kéo dài cửa sổ để che lỗi.

## Chạy lại — không cần build firmware

Dừng publisher/camera cũ. Giữ Wokwi chạy, đưa local về nền: MQ ADC<1700, LDR ADC≥750, DHT28°C/45%; hết nguy hiểm đủ3giây mô phỏng rồi thả/nhấn ACK mới để về NORMAL. Chờ mạng1/1/1/1.

Mã firmware đang có bằng chứng là `R7-ff4ea6a0f5395c1c`. Nếu boot hiển thị mã khác, thay mã ở cả hai lệnh bằng mã thật; không bỏ identity check.

**Terminal A — capture, để tiếp tục chạy:**

```sh
.venv/bin/python tools/capture_mqtt.py \
  --out runs/replay-clock-01.jsonl --duration 180 \
  --expected-firmware-id R7-ff4ea6a0f5395c1c \
  --ai-clock-domain WOKWI_SIMULATED_UTC
```

Chờ `[CAPTURE ready]`, mở **terminal B riêng ngay lúc terminal A vẫn đang chạy**:

```sh
.venv/bin/python tools/ai_publish.py \
  --backend replay --interval 5 \
  --wokwi-clock \
  --expected-firmware-id R7-ff4ea6a0f5395c1c \
  --log runs/replay-clock-publisher-01.jsonl
```

Dùng tên file mới nếu đã tồn tại. Không cần restart Wokwi chỉ để bật mapper; nếu restart ESP khi publisher đang chạy, hãy dừng và chạy lại publisher.

Mong đợi publisher báo `SIMULATION_CLOCK_MODE`, sau đó4PUBACK và1UNAVAILABLE; mỗi PUBACK có `clock_mapping.timestamp_domain=WOKWI_SIMULATED_UTC`. ESP tăng bộ đếm Nhan so với trước lượt, không tăng lỗi TIMESTAMP mới; với local0: NORMAL→WARNING→FIRE_SUPPRESSION→RECOVERY. Log định kỳ có thể bỏ lỡ state ngắn, dùng EVENT/capture đối chiếu. An toàn3giây mô phỏng + ACK mới để về NORMAL. Chưa kết luận tải/cửa thật chỉ từ log lệnh.

Nếu timeout chờ telemetry: kiểm tra Wokwi có đang chạy, đúng topic/firmware và tốc độ mô phỏng. Không hạ ngưỡng AI để sửa lỗi thời gian.

Đọc capture sau lượt:

```sh
.venv/bin/python tools/s8_track.py capture-summary --capture runs/replay-clock-01.jsonl
```

Summary hiển thị clock domain do người thao tác khai báo; không tự đánh PASS. Capture chỉ có telemetry/event ESP, cần giữ publisher JSONL để biết bản tin được ánh xạ ra sao.

## Sau khi replay nhận được, dùng model thật

Đây là lựa chọn bước sau, không cần thử thêm ảnh. Chạy cùng capture có `--ai-backend MODEL_UNVERIFIED` và cùng clock domain, rồi dùng:

```sh
.venv-ai/bin/python tools/ai_publish.py \
  --backend plugin --plugin yolo_plugin:predict --source 0 \
  --model-id rabahdev-fire-smoke-yolov8n-13017fe8 --interval 1 \
  --wokwi-clock --expected-firmware-id R7-ff4ea6a0f5395c1c \
  --log runs/model-clock-publisher-01.jsonl
```

Model vẫn phải đủ confidence0,8 mới phát; UNAVAILABLE không đổi thành bình thường. Chế độ clock không nâng confidence, không tạo phát hiện giả. Lịch lấy ảnh có thể chậm lại để chờ mốc telemetry mới.

Nguồn: [Wokwi: simulation clock có thể chậm hơn wall clock](https://docs.wokwi.com/guides/esp32-wifi#viewing-wifi-traffic-with-wireshark). Các kiểm tra localhost dùng PCfixture, không được coi là nghiệm thu MCU hoặc độ chính xác model.
