# Firmware PCCC Nhóm 07 INT1461 — LOCAL R5

**S2–S4 đã có code, build ESP32 và test tự động pass. S5 chưa xác nhận runtime Wokwi.** Theo dõi duy nhất tại [KB](docs/KB.md); thao tác test tại [hướng dẫn R5](docs/phase2-testing.md). Chưa có MQTT/AI/dashboard. DOCX chưa sửa.

## Chạy

Mở thư mục firmware trong VS Code, terminal tại đây:

```sh
/Users/daianhdung/.platformio/penv/bin/pio run
python3 test/run_host_tests.py
```

Máy khác dùng `pio run` khi PlatformIO trong PATH. Stop hẳn Wokwi rồi Start Simulator để nạp cả firmware/diagram mới. Log phải có `LOCAL R5: LDR + SERVO + DHT HOLD`; mạch có LDR và servo thay nút đỏ, nút xanh ACK LOCAL R5. Không cần upload USB.

## Thiết kế đã triển khai

| Khối | Kết nối/hành vi |
|---|---|
| ESP32 | DOIT DevKit V1; espressif32@7.0.1, Arduino core2.0.17 |
| MQ2 | AOUT→GPIO35; ADC1s,1800warning/2800danger; ngưỡng xuống<1700/<2700 |
| LDR | AO→GPIO32, nguồn3V3;100ms; sáng tăng→ADC giảm;≤500lửa giả,≥750giải trừ |
| DHT22 | DATA4/3V3/pull-up10k;3s;55°C clear<53°C,rate≥2°C/s |
| Servo cửa | PWM33/V+VIN/GND;50Hz16bit/LEDC8 group1;0°đóng/90°mở |
| Còi | GPIO27/LEDC0 group0/2kHz, không chung timer servo |
| Relay bơm/van | GPIO26/25,npn HIGH bật; LED tải cam qua COM-NO |
| ACK | GPIO19 activeLOW;debounce50ms,an toàn3s+cạnh nhấn mới |
| LCD / LED | I2C21/22,0x27;đỏ14/xanh13 |

Cửa mở khi FIRE, giữ mở ở RECOVERY, đóng sau ACK hợp lệ; WARNING trước FIRE không mở. Giữ nguyên nhân nhiệt cao/rate khi DHT lỗi hoặc stale, chỉ mẫu hợp lệ giải trừ; rate NaN không tự xóa chốt. Bơm vẫn dừng ở60s và khóa tái kích tới ACK an toàn. Mặc định log chữ gọn mỗi3giây (EVENT in ngay), có CSV37cột nếu chọn Csv trong config.h rồi build. Servo/relay trên log là lệnh, chưa có feedback điện.

## Kiểm chứng

[Build R5](docs/evidence/local-r5-build.log), [host/wiring tests](docs/evidence/local-r5-host-test.log), [hash](docs/evidence/local-r5-sha256.json), [giới hạn runtime](docs/evidence/local-r5-runtime-status.txt). Host tests có regression mất DHT, policy cửa, LDR hysteresis và20.000bước tổng hợp; không thay260lượt Wokwi cuối. Truy cập VSCode qua CUA timeout nên chưa có ảnh/log MCU R5 hoặc số đo latency.

Ngưỡng LDR là tham số demo ban đầu, cần kiểm tra S5 theo ADC thực. LDR không phải cảm biến lửa IR; ADC MQ chưa phải ppm. Không phát hiện mọi lỗi đứt dây analog bằng range/stale check. Mạch chỉ mô phỏng; phần cứng thật cần thiết kế nguồn/chuyển mức/tải/warmup/hiệu chuẩn riêng.

Tài liệu tổng và bảng260lượt nằm ở thư mục cha repo firmware; khi nộp phải gom đầy đủ model/dataset/báo cáo/minh chứng. Không tự commit/push hoặc chuyển .git. Mô hình học thuật không thay thiết bị PCCC đạt chuẩn.
