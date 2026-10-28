> Bản hiện tại là R7, bổ sung identity/capture/adapter/S8. Xem [hướng dẫn S7–S8](../s7-s8-guide.md). Contract AI v1 và các ca thử S6 bên dưới vẫn áp dụng; boot header R6 là lịch sử.

# S6 — MQTT và mock, bản R6

S5 được **hoãn theo yêu cầu người dùng**, không đánh PASS. Bản này triển khai giao thức và hợp nhất AI, **chưa có model/camera**. Không thay sơ đồ, GPIO hoặc default gas10ppm/còi0.25. Thông số local/timeout/ACK vẫn giữ nguyên.

## Flow qua từng file

1. `main.cpp` đọc cảm biến, lấy bản sao network mới nhất bằng queue không chờ.
2. `network.cpp`: task riêng core0 khởi tạo Wi-Fi/NTP/ESP-MQTT. Task của MQTT quản lý socket/callback; callback chỉ copy tối đa256byte vào queue4phần tử. Worker đọc tối đa4bản tin/mỗi50ms.
3. `ai_contract.cpp`: kiểm tra JSON/schema/nhãn/confidence/giờ UTC/replay; gói lỗi không gia hạn mẫu trước. ArduinoJson được pin6.21.5.
4. `safety.cpp`: `merged=max(local, ai.fresh ? ai.level : 0)`. FSM cũ tiếp tục quyết định tải, timeout60s và ACK. Không có lệnh MQTT bật bơm/đóng cửa/reset trực tiếp.
5. `outputs.cpp` chạy trước LCD/log/network enqueue; không có socket/DNS/reconnect trong vòng local.
6. `mqtt_payload.cpp` tạo JSON telemetry/event trong worker, số đo không hợp lệ là `null`. `telemetry.cpp` và `display.cpp` hiển thị trạng thái mạng/AI.
7. `tools/mqtt_mock.py` đóng vai publisher AI giả lập hoặc subscriber theo dõi ESP; model thật sẽ thay publisher này ở S7.

## Cấu hình và phiên bản

- Board DOIT DevKit V1; espressif32@7.0.1, Arduino core2.0.17; dùng **ESP-MQTT có sẵn trong SDK ESP-IDF4.4.x**, không dùng PubSubClient.
- Thư viện JSON ArduinoJson6.21.5, Python paho-mqtt2.1.0. Broker dùng trong smoke test máy chủ: amqtt0.11.3 trên localhost, chưa phải ESP32.
- Mặc định bật mạng, SSID `Wokwi-GUEST`, password rỗng. Broker demo `mqtt://broker.hivemq.com:1883`, prefix `ptit/nhom07/lab-7c49e2`. Chưa chứng minh ESP32 kết nối broker công cộng này trong Wokwi. Broker demo công cộng/plaintext chỉ dùng dữ liệu mô phỏng; không có bảo đảm riêng tư/xác thực hoặc SLA.
- Đổi cấu hình: copy `include/secrets.example.h` thành `include/secrets.h` (Git ignore), đặt broker/SSID/prefix/credentials rồi build. Chọn prefix riêng cho mỗi nhóm/lượt để tránh nhận dữ liệu của nhau. ClientID gồm hash deployment và MAC để giảm xung đột giữa deployment.
- Muốn quay về local-only: `#define PCCC_NETWORK_ENABLED 0` trong secrets.h và build; không đổi GPIO/FSM.
- Wokwi Public Gateway truy cập broker internet, không truy cập broker localhost của máy. Muốn test ESP với broker trên máy cần cấu hình gateway phù hợp; không dùng127.0.0.1 làm địa chỉ broker của ESP rồi kỳ vọng nó là máy Mac.

## Hợp đồng v1

Ví dụ (phải dùng timestamp **hiện tại**, không copy số cố định để gửi):

```json
{"v":1,"nhan":"lua","do_tin_cay":0.93,"ts_ms":1793152800000}
```

| Trường | Điều kiện |
|---|---|
| v | Integer1; đúng4trường, không có trường lạ/trùng |
| nhan | String `lua`, `khoi`, `binh_thuong` |
| do_tin_cay | Số hữu hạn[0,1], không nhận string/bool/null |
| ts_ms | Integer Unix UTC milliseconds, đồng hồ PC/ESP phải đúng |

Tối đa256byte. Tuổi lúc nhận phải<15s, tương lai cho phép≤2s. UTC chưa hợp lệ (trước2024) thì rejectCLOCK_UNSYNCED, local vẫn chạy và MQTT vẫn có thể kết nối. Chấp nhận **ts_ms tăng nghiêm ngặt** trong một luồng publisher/deployment: duplicate/cũ hơn rejectREPLAY. Watermark giữ qua reconnect, không lưu qua reboot; UTC/TTL và reject retained giới hạn dữ liệu cũ sau reboot. Nếu PC đổi giờ lùi có thể phải chờ vượt watermark, không tự xóa watermark để nhận lại gói cũ.

Confidence≥0.8: lua→2, khoi→1, binh_thuong→0. Confidence thấp vẫn là heartbeat có schema hợp lệ nhưng level0; không phải bằng chứng cảnh chắc chắn an toàn. Mẫu gần hết hạn chỉ còn thời gian TTL còn lại; receipt millis là giới hạn đơn điệu, quay vòng millis đã có host test. Gói sai giữ nguyên mẫu tốt trước tới khi hết TTL. Mất mạng/session mới vô hiệu freshness, không dùng lại mẫu session trước. Mất AI không tự tắt nguy hiểm local; nếu AI là nguồn duy nhất, merged giảm dẫn tới RECOVERY, cửa giữ mở và vẫn cần an toàn3s + cạnh ACK mới.

| Topic (prefix + hậu tố) | Chiều | QoS gửi/subscribe | Retained |
|---|---|---|---|
| `/ai/result` | Python→ESP | Mock publish1; ESP subscribe1 (broker có thể grant0/1) | false |
| `/device/esp32-01/telemetry` | ESP→PC | publish0 | false |
| `/device/esp32-01/event` | ESP→PC | publish0 | false |
| `/device/esp32-01/availability` | ESP/broker→PC | online publish0; LWT offline1 | true |

Đây là MQTT3.1.1. Reject retained **delivery** dựa vào cờ broker gửi khi subscribe lại. Broker có thể chuyển một live publish có retain=true tới subscriber hiện tại với retain=false, nên không thể xác định ý định retain của publisher từ mọi live delivery. Test retained bằng cách lưu gói, nối lại ESP trongTTL và quan sátRETAINED; sau test phải xóa gói retained. Publisher/model chỉ dùng retain=false. Có thể mất/duplicate bản tin; QoS1 không bảo đảm mọi kết quả cấp hệ thống. Subscribe lại sau mỗi CONNECTED, chỉ bật cờSub khi SUBACK grant0/1; reject grant0x80 và reconnect sau timeout.

Wi-Fi retry mỗi30s; MQTT backoff1→2→4→8→16→30s (có thể bắt đầu2s sau lần fail đầu), connect attempt watchdog12s, SUBACK timeout10s. Socket timeout5s nằm trong worker, không trong local loop. Telemetry queue1 ghi đè bằng mẫu mới, event queue8drop khi đầy, RX queue4drop khi đầy; không block local. ESP publishQoS0 không giữ application retransmission outbox. Telemetry/event có counter mất/lỗi, không tuyên bố lưu mọi event. Event có uptime lúc ghi, `ts_ms` lúc publish và `queue_age_ms`; event bị trễ không phải lệnh điều khiển.

JSON publish có v1, modeSIMULATION, state/source/latched_source, local_level/ai_level/merged_level, active/latched masks, dữ liệu cảm biến/null, lệnh đầu ra, AI freshness/counters, max_loop_gap_ms. Source có NONE/LOCAL/AI/LOCAL+AI; ACK_SAFE là thao tác operator theo transition_reason. Serial CSV nay39cột, tên cột mức hợp nhất đổi `local_level`→`merged_level`, thêm `local_rule_level,ai_level` cuối; không dùng parser37cột cũ. Reasonmask thêm256=AI_SMOKE,512=AI_FIRE.

## Test nhanh, không cần hoàn tất S5 trước

Terminal ở thư mục **firmware**:

```sh
/Users/daianhdung/.platformio/penv/bin/pio run
python3 -m venv .venv
.venv/bin/python -m pip install -r tools/requirements-mqtt.txt
```

1. Stop/Start Wokwi. Boot phải ghi `S6 R6`. Chờ dòng `WiFi/MQTT/Sub/UTC: 1/1/1/1`; AI=UNAVAILABLE trước khi có publisher là đúng, không phải lỗi local. NếuTaskOFF dù enabled, cần kiểm tra cấp phát/task init; nếuMQTT1/Sub0 là chưa có subscription.
2. Giữ local nền (MQ ADC<1700, LDR≥750, DHT28/45); nếu còn latch cũ thì ACK an toàn như trước.
3. TerminalA xem ESP:

```sh
.venv/bin/python tools/mqtt_mock.py --watch
```

4. TerminalB gửi lửa giả lập từ PC trong10s:

```sh
.venv/bin/python tools/mqtt_mock.py --label lua --count 5 --interval 2
```

Mong đợiFIRE_SUPPRESSION, local0/AI2, sourceAI, tải bật/cửa mở. Đây là **mock gây báo động để test**, không phải camera phát hiện lửa. Sau gói cuối, đợi hếtTTL (tối đa15s từ gói cuối, có thể sớm hơn do tuổi gói): AI unavailable, RECOVERY, tải tắt/cửa giữ mở; ACK an toàn đưaNORMAL/cửa đóng.

5. Gửi khói hoặc bình thường:

```sh
.venv/bin/python tools/mqtt_mock.py --label khoi
.venv/bin/python tools/mqtt_mock.py --label binh_thuong
```

Khói→WARNING khi local0. AI bình thường không hạ MQ/LDR/nhiệt local nguy hiểm. Confidence thấp test bằng `--label lua --confidence 0.5`, AI fresh nhưng level0.

6. Negative cases (chạy từng lệnh, xem counters/lastReject, mẫu tốt cũ không được gia hạn):

```sh
.venv/bin/python tools/mqtt_mock.py --case json
.venv/bin/python tools/mqtt_mock.py --case missing
.venv/bin/python tools/mqtt_mock.py --case type
.venv/bin/python tools/mqtt_mock.py --case confidence
.venv/bin/python tools/mqtt_mock.py --case old
.venv/bin/python tools/mqtt_mock.py --case future
.venv/bin/python tools/mqtt_mock.py --case duplicate --count 3
.venv/bin/python tools/mqtt_mock.py --case oversize
```

Oversize/fragment bị drop tại callback nên tăngdrop thay vìrejectparser. Duplicate chỉ gói đầu có thể được nhận; hai gói còn lại phảiREPLAY. Không chạy các case này rồi tự tính toàn bộS6 pass nếu chưa đối chiếu log.

## Checklist runtime S6 chưa chạy trên ESP

- [ ] Boot không Wi-Fi/broker down, kích LDR/MQ vẫn điều khiển local; so sánhSerialMaxloopgap có/không mạng. Maxloopgap không phải đo latency vật lý.
- [ ] Broker/Wi-Fi rớt rồi nối lại: subscribe lại, tiếp tục nhận gói mới, không tái dùng AI cũ; PCwatch vẫn nhậntelemetry/event/availability.
- [ ] NTP chưa có: CLOCK_UNSYNCED, không nhận AI; khi UTC hợp lệ thì gói mới được nhận.
- [ ] AI kích khi local nền, TTL và low-confidence; local danger + AI normal; đồng thời local/AI, source/mask đúng.
- [ ] Gói lỗi/cũ/tương lai/trùng/retained không gia hạn; flood có giới hạn bộ nhớ/queue, local vẫn phản hồi.
- [ ] Giữ AI lửa bằng `--count 40 --interval 2`: sau60s tải tắt/lock, AI mới vẫn không bật lại; ACK khi nguy hiểm không reset.
- [ ] Retained: dừng ESP, publish `--case retained`, Start lại nhanh trongTTL; rejectRETAINED. Sau đó `--case clear-retained` để xóa. Chờ NTP không được dùng làm lý do bỏ qua kiểm tra cờretained trong host test.
- [ ] Lưu hash firmware/model(mock), log và ảnh; không điền kết quả13×20từ những smoke tests này.

## Kiểm tra tự động và bằng chứng

```sh
python3 test/run_host_tests.py
python3 -m unittest discover -s test -p 'test_mqtt_mock.py'
```

Broker smoke tùy chọn (Python≥3.10, venv riêng; amqtt chỉ phục vụtest):

```sh
.venv/bin/python -m pip install -r tools/requirements-test-mqtt.txt
.venv/bin/python test/broker_smoke.py
```

[Build ESP32](../evidence/s6-build-2026-10-28.log), [host core/parser/fusion/encoder](../evidence/s6-host-2026-10-28.log), [Python mock unit](../evidence/s6-mock-unit-2026-10-28.log), [localhost broker smoke](../evidence/s6-broker-smoke-2026-10-28.log). Broker smoke là PC↔broker↔PC, không chạy ESP32/model. Runtime Wokwi, reconnect/flood và latency vẫn NOT_RUN; S5 hoãn không biến thànhPASS.

Nguồn API: [ESP-MQTT SDK4.4](https://docs.espressif.com/projects/esp-idf/en/v4.4.7/esp32/api-reference/protocols/mqtt.html), [ArduinoJson strict types](https://arduinojson.org/v6/api/jsonvariant/is/), [Paho2](https://eclipse.dev/paho/files/paho.mqtt.python/html/client.html), [Wokwi networking](https://docs.wokwi.com/guides/esp32-wifi). Có tham khảo thêm headerMQTT đi kèm package build thực, không áp dụng layout configIDF5.x vào Arduino core2.x.
