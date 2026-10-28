# Firmware PCCC Nhóm07 — S7/S8 R7

**Đã có phần mềm tích hợp và công cụ kiểm thử tới S8 bằng mock. Model YOLOv8n đã chạy thử local ở chế độ quan sát, chưa nghiệm thu với ESP32.** S5 hoãn. S8 chưa hoàn tất nghiệm thu260lượt. [Tiến độ và checklist duy nhất](docs/KB.md#progress) · [Hướng dẫn hiện tại S7–S8](docs/s7-s8-guide.md) · [Contract MQTT S6](docs/reference/s6-mqtt-contract.md).

## Bắt đầu tại đây

1. TrongVSCode chọn **File → Open Workspace from File…** và mở [PCCC.code-workspace](PCCC.code-workspace).
2. Đọc [bản đồ thư mục và vai trò từng file](docs/project-map.md).
3. Xem [checklist S0–S9](docs/KB.md#progress), rồi thực hiện một lượt capture/replay theo hướng dẫn hiện tại.

Workspace chỉ mở repo `firmware`, ẩn thư mục build/môi trườngPython; có sẵn task **Build ESP32** và **Kiểm tra phần mềm**. Hướng dẫnR5 nằm trong `docs/archive/`; contractMQTT nằm trong `docs/reference/`; hướng dẫn dùng hiện tại là `docs/s7-s8-guide.md`.

## Chạy

Mở thư mục firmware trong VS Code. Build rồi Stop/Start Wokwi:

```sh
/Users/daianhdung/.platformio/penv/bin/pio run
```

Máy khác dùng `pio run` khi PlatformIO có trong PATH. Boot phải có `S7/S8 R7` và `Firmware: R7-<hash>`. Firmware tự tạo boot_id, MQTT có firmware_id để kiểm tra đang thu đúng bản. Không cần upload USB. Default MQ10ppm, LDR100lux, DHT28°C/45%, còi volume0.25; nếu simulator còn giữ slider cũ, đưaMQADC<1700 và LDRADC≥750, ACK an toàn khi cần.

## Một lệnh kiểm tra phần mềm

```sh
.venv/bin/python tools/verify_project.py
```

Build/core/Python/scenarios được chạy và lưu report/log/hash trongruns/. Không chạy Wokwi hoặc model. Bộ host có240PASS/20DEFERRED là test logic bằng virtualmillis, không phải240lượt nghiệm thu Wokwi. [Báo cáo đã chạy](docs/evidence/s7s8-final-checks-2026-10-28/report.json).

## Quan sát AI thật trên máy tính

Model YOLOv8n lửa/khói đã nạp và người dùng đã thử ảnh/webcam; chưa đánh giá độc lập hoặc nghiệm thu tích hợp với ESP32. Chạy quan sát, không gửi MQTT:

```sh
.venv-ai/bin/python tools/ai_observe.py
```

Xem [cách đọc confidence, lưu ảnh và log báo giả](docs/ai-observation.md). Ngưỡng hiển thị 0,25, ngưỡng chọn 0,8; chưa lọc nhiều frame. Không phát hiện không tự kết luận an toàn.

## Thu log và thử replay

Nếu Wokwi từ chối `TIMESTAMP`, dùng [chế độ đồng hồ mô phỏng](docs/wokwi-clock.md) thay các lệnh UTC mặc định bên dưới. Capture và publisher cần chạy đồng thời ở hai terminal.

Môi trường .venv có Paho2.1.0; nếu chưa có, tạo venv rồi cài `tools/requirements-mqtt.txt`. Chờ log `WiFi/MQTT/Sub/UTC: 1/1/1/1`, terminalA:

```sh
.venv/bin/python tools/capture_mqtt.py --out runs/s8-demo-01.jsonl --duration 60
```

TerminalB:

```sh
.venv/bin/python tools/ai_publish.py --backend replay --interval 5
```

Đây là kết quả AI viết sẵn, có thể kích còi/bơm/van/cửa trong mô phỏng. Camera/model lỗi hoặcunknown không tự phát nhãn bình thường. [Đọc log, thay model bằng plugin và ghi nghiệm thu](docs/s7-s8-guide.md).

```sh
.venv/bin/python tools/s8_track.py capture-summary --capture runs/s8-demo-01.jsonl
.venv/bin/python tools/s8_track.py status
```

Mỗi capture dùng tênfile mới. Bảng260lượt gốc ởthư mục cha `../tests/integration-results.csv`; không tạo bảnPASS song song. Model thật/dataset/metrics/TC11 và lượt MCU còn chờ. DOCX/S9 chưa sửa.

## Thiết kế giữ nguyên

| Khối | Kết nối/hành vi |
|---|---|
| ESP32 | DOIT DevKitV1; espressif32@7.0.1, Arduino core2.0.17 |
| MQ2 | AOUT→GPIO35; đọc1s, warning1800/danger2800ADC, clear<1700/<2700 |
| LDR | AO→GPIO32/3V3;100ms, ADC≤500lửa giả/≥750giải trừ |
| DHT22 | DATA4/3V3/pull-up10k;3s;55°C clear<53°C, rate≥2°C/s |
| Servo | PWM33/V+VIN/GND;50Hz16bit,LEDC8/group1;0°đóng/90°mở |
| Còi | GPIO27/LEDC0/group0/2kHz, timer khác servo |
| Relay bơm/van | GPIO26/25,npn HIGH bật; tải quaCOM-NO |
| ACK | GPIO19 activeLOW, debounce50ms, an toàn3s+cạnh nhấn mới |
| LCD/LED | I2C21/22,0x27; đỏ14/xanh13 |

AI chỉ nâng mức qua max(local,AI hợp lệ), không trực tiếp bypassFSM/timeout/ACK. Cửa mở khi FIRE, giữ RECOVERY, đóng sau ACK hợp lệ. Bơm dừng ở60s và khóa tớiACK an toàn; giữ nguy hiểm nhiệt khiDHT lỗi. LogSerial3s vàEVENT ngay; CSV39cột. Lệnh trênlog chưa phải feedback cơ khí/tiếp điểm.

Mặc định mạng Wokwi-GUEST, broker demo HiveMQ:1883, prefix `ptit/nhom07/lab-7c49e2`. Copy `include/secrets.example.h`→`include/secrets.h` để cấu hình riêng (Gitignore), dùng prefix riêng mỗi nhóm. Socket/DNS ở network task; chưa nghiệm thu latency MCU khi mạng lỗi. SetPCCC_NETWORK_ENABLED0 rồi build để local-only.

Mạch là mô phỏng học thuật. ADCMQ chưa hiệu chuẩn ppm, LDR là demo không phải cảm biến lửa IR, chưa phát hiện mọi lỗi dây. Phần cứng thật cần thiết kế/hiệu chuẩn riêng. Source/state/test được lưu, không dùng host/mock thay các bằng chứng thực còn thiếu.
