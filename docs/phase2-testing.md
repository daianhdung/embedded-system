# Test local R5 trên Wokwi — S2 đến S5

Bản R5 đã thêm LDR và servo, sửa giữ nguy hiểm nhiệt khi DHT mất dữ liệu. Build và test tự động không thay runtime. **S5 chưa được xác nhận**: công cụ truy cập VS Code timeout; chưa thu được ảnh/log chạy simulator của bản này. Không tính các bước dưới thành 260 lượt nghiệm thu khi chưa chạy và lưu từng lượt.

## 1 Nạp đúng bản

Mở thư mục firmware trong VS Code. Trong terminal ở thư mục đó:

```sh
/Users/daianhdung/.platformio/penv/bin/pio run
```

Máy khác dùng `pio run` khi có trong PATH. Stop hẳn Wokwi, đóng tab simulator rồi chọn `Wokwi: Start Simulator`. Nếu mạch cũ còn hiện, Reload Window rồi Start lại. Boot log mới phải có:

```text
=== LOCAL R5: LDR + SERVO + DHT HOLD | PHASE 2 ===
```

Mạch mới có module LDR thay nút đỏ, servo cửa và nút xanh `ACK LOCAL R5`; vẫn giữ hai relay và hai LED tải cam BOM/VAN. Không cần upload vào thiết bị USB để chạy simulator.

## 2 Dây và tham số hiện dùng

| Khối | Chân nối | Tham số |
|---|---|---|
| MQ2 | AOUT→D35, VCC→VIN, GND chung | ADC1; đọc1s; cảnh báo1800/nguy hiểm2800; giải trừ<1700/<2700 |
| LDR | AO→D32, VCC→3V3, GND chung | ADC1; đọc100ms; ADC≤500→lửa giả, ADC≥750→hết lửa giả |
| Servo cửa | PWM→D33, V+→VIN, GND chung | LEDC kênh8/group1,50Hz/16bit; 0° đóng,90° mở |
| Còi | D27 | LEDC kênh0/group0,2kHz; timer khác nhóm servo |
| DHT22 | DATA→D4, nguồn3V3, pull-up10k | Đọc3s; stale6,5s; nhiệt55°C/giải trừ<53°C; rate2°C/s |
| ACK | D19→nút→GND | INPUT_PULLUP, debounce50ms; an toàn3s + lần nhấn mới |
| Hai relay | D26 bơm / D25 van | npn HIGH bật; LED tải qua COM-NO |
| LCD / LED | D21/D22 / D14,D13 | LCD0x27; đỏ/xanh |

Sáng tăng làm **ADC LDR giảm** theo mạch chia áp của module. Ngưỡng500/750 là tham số demo ban đầu; chưa phải ngưỡng cháy hoặc lux đã hiệu chuẩn. Thử theo ADC thực hiển thị thay vì khẳng định một mức lux luôn cho cùng ADC. Không đổi ngưỡng chỉ để ép test pass; nếu cần điều chỉnh phải ghi khảo sát và lý do trong KB.

LDR không phân biệt lửa với đèn sáng. Mạch và mức nguồn ở đây chỉ cho simulator; chưa phải thiết kế hardware nguồn/chuyển mức/servo tải thật đã kiểm chứng. Không phát hiện được mọi trường hợp đứt dây analog chỉ bằng ADC: đầu vào hở có thể vẫn trả giá trị trong dải.

## 3 Bắt đầu ở nền

1. Chọn LDR, đặt ánh sáng khoảng100lux (mạch mặc định100lux). Xem log LDR, bảo đảm ADC≥750 và không phát hiện lửa giả.
2. MQ mặc định10ppm khi Stop/Start mới (đã hạ từ400ppm để khởi động yên lặng). Kiểm tra ADC<1700; nếu slider đang giữ giá trị của lượt cũ, hạ MQ về nền. DHT28°C/45%; thả ACK. Đợi DHT đọc tốt.
3. Nếu đã có báo động do giá trị ban đầu, đợi đầu vào an toàn3s rồi thả/nhấn ACK mới >0,1s. Hệ phải NORMAL, xanh sáng, hai LED tải và còi tắt; cửa lệnh0°.

## 4 Test theo thứ tự

| Test | Thao tác | Kết quả cần thấy |
|---|---|---|
| R5-01 Nền | Làm mục3 | NORMAL, xanh; relay/còi tắt, cửa0° |
| R5-02 Warning | LDR nền, MQ lên ADC1900–2400 | WARNING, đỏ/còi; tải tắt, cửa vẫn0° |
| R5-03 Warning về nền | MQ<1700 | RECOVERY giữ đỏ; cửa vẫn đóng vì chưa từng FIRE; an toàn3s + ACK mới →NORMAL |
| R5-04 LDR | MQ nền; tăng ánh sáng mạnh, thử20000lux hoặc tăng tới khi ADC≤500 | FIRE_SUPPRESSION, nguồn local/FLAME, tải BOM/VAN sáng, còi/đỏ; cửa lệnh90° và quan sát servo thực |
| R5-05 LDR biên | Khi đã có lửa giả, chỉnh ADC khoảng501–749 rồi≥750 | Trong vùng giữa vẫn giữ lửa giả; ≥750 thì RECOVERY, bơm/van/còi tắt; cửa vẫn90° |
| R5-06 ACK/cửa | Từ R5-05, đầu vào an toàn3s, thả rồi nhấn ACK mới | NORMAL, xanh, cửa đóng0°. Nhấn lúc còn nguy hiểm không được đóng cửa/reset |
| R5-07 MQ danger | LDR nền, MQ≥2800 | FIRE, cả hai relay bật, cửa mở; hạ MQ<1700 rồi ACK theo quy trình |
| R5-08 Nhiệt tuyệt đối | MQ/LDR nền, DHT56°C | FIRE vì nhiệt (có thể cả rate), cửa mở. Hạ28°C, chờ mẫu tốt/rate hết nguy hiểm, RECOVERY và ACK |
| R5-09 Rate | DHT28°C ổn định, đổi35°C trước lần đọc kế | Có thể rate≥2°C/s theo dt thực và FIRE. Giữ35°C đến mẫu tiếp theo để rate về0; phục hồi/ACK |
| R5-10 Timeout | Giữ LDR hoặc MQ nguy hiểm liên tục, tính từ event FIRE | Đủ60s: RECOVERY, tải tắt, cửa vẫn mở; giữ tiếp10s không tái bật. ACK khi còn nguy hiểm không đóng. Hết nguy hiểm +3s + ACK mới →NORMAL/cửa đóng |
| R5-11 Nhấn giữ | Giữ ACK từ boot hoặc nhấn sớm rồi giữ qua3s an toàn | Không tự reset; cần thả rồi nhấn mới khi ackReady |
| R5-12 DHT lỗi từ boot | Stop, tạm ngắt DATA DHT trong diagram rồi build nếu code đổi/Start | Sau grace báo DHT_FAULT; chưa có nhiệt nguy hiểm thì cửa không tự mở chỉ vì fault. LDR/MQ vẫn kích FIRE |
| R5-13 Đồng thời servo/còi | Lặp FIRE→RECOVERY→ACK→FIRE vài lượt | Còi vẫn phát đúng, servo không rung/đổi góc do đổi tần số còi; hai relay đúng trạng thái |

Nếu ngắt dây khi **Stop rồi Start**, MCU mất lịch sử trước đó, nên không chứng minh được regression “nhiệt nguy hiểm→DHT mất dữ liệu trong cùng lần chạy”. Regression này đã được thử trên core bằng dữ liệu tổng hợp. Nếu giao diện simulator cho ngắt DATA trong lúc chạy, có thể thử sau khi đã có mẫu60°C: bơm không dừng chỉ do DHT lỗi, log GIU NGUY HIEM NHIET; vẫn dừng ở60s và cửa mở. Không khẳng định đã thử được ngắt nóng nếu giao diện không hỗ trợ. Khôi phục dây DATA sau thử lỗi.

Các lịch là danh nghĩa; DHT/I2C/Serial vẫn có thời gian đồng bộ. Chưa có phép đo latency runtime R5.

## 5 Đọc log

- `Khoi (ADC)` và `LDR (ADC)` là hai kênh khác nhau. LDR sáng hơn thì ADC thấp hơn.
- `Lua LDR gia`: kết quả hysteresis; không phải phát hiện lửa IR thật.
- `Cua (lenh)`: MO90°/DONG0°; chưa có feedback vị trí. Phải quan sát servo trong Wokwi.
- `GIU NGUY HIEM NHIET`: mất DHT hoặc chưa có rate hợp lệ để xác nhận giải trừ nguyên nhân nhiệt đã biết. Không đồng nghĩa bơm được chạy quá60s.
- `Khoa timeout`: đã dừng bơm vì hết hạn, chưa cho tái kích trước ACK an toàn.
- `Bom / van`: lệnh, đối chiếu LED tải COM-NO.

Mặc định log Readable gọn, mỗi3giây một snapshot, gom2–3thông số/dòng; EVENT chuyển state vẫn in ngay. Lịch cảm biến/FSM không đổi. Muốn thu CSV, đổi `kSerialLogFormat` trong config.h sang Csv rồi build; Both in cả hai. CSV R5 giữ30cột đầu và thêm7cột: ldr_adc,ldr_valid,ldr_sample_ms,ldr_age_ms,door_open,door_angle_cmd,thermal_unconfirmed. Tổng37cột. Không trộn boot ROM vào file CSV.

Mask:1=SMOKE_WARNING,2=SMOKE_DANGER,4=FLAME giả từLDR,8=TEMPERATURE,16=TEMP_RISE,32=DHT_FAULT,64=FAST_FAULT MQ,128=LDR_FAULT (thiếu/già mẫu phần mềm, không bảo đảm bắt mọi lỗi dây vật lý).

## 6 Ghi kết quả

Lưu từng lượt: testID, firmware/hash, đầu vào, expected, observed, pass/fail, ảnh/log và ghi chú. Cập nhật [KB](KB.md) S5/L01–L10 khi có đủ bằng chứng; không đánh PASS cả13×20 từ một lượt smoke test. Host test ở `python3 test/run_host_tests.py` kiểm tra logic thuầnC++ và wiring, không chạy MCU/mô phỏng cơ khí.

Nguồn: [LDR Wokwi](https://docs.wokwi.com/parts/wokwi-photoresistor-sensor), [pin AO LDR](https://github.com/wokwi/wokwi-elements/blob/main/src/photoresistor-sensor-element.ts), [servo](https://docs.wokwi.com/parts/wokwi-servo), [LEDC core2.0.17 — mapping nhóm/kênh/timer](https://github.com/espressif/arduino-esp32/blob/2.0.17/cores/esp32/esp32-hal-ledc.c). Không áp dụng nhầm API core3.x cho môi trường core2.0.17 đã chốt.

## Chẩn đoán âm thanh và servo ngày28/10/2026

Buzzer hiện volume0.25 (đã tăng0.1→0.5 khi chẩn đoán rồi giảm theo yêu cầu người dùng). Sau build/Stop-Start phải có boot line AUDIO DIAG và dòng PWM doc lai mỗi3s. FIRE mong đợi coi2000Hz/cua50Hz/duty4915; NORMAL coi0Hz/cua50Hz/duty1638. Đây là readback thanh ghi, chưa đo sóng điện hoặc chuyển động. Nếu còi lệnhBAT nhưng0Hz, gửi log để kiểm tra driver; nếu2000Hz mà không nghe, kiểm tra âm lượng/mute củaVSCode/thiết bị phát rồi gửi ảnh buzzer. Mở/đóng servo phải đối chiếu cặp lệnh0/90vàquan sát tay servo. Giữ MQ<1700 khi test riêngLDR; logMQ3543vẫn là nguồn nguy hiểm dù hạLDR.


## Bố cục sơ đồ ngày28/10/2026

Bản cuối chia INPUT bên trái (gồm DHT22), ESP32 giữa, LCD/relay/servo bên phải; STATUS/ALARM riêng cho còi và LED. Mọi nguồn được ghi rõ tại chỗ: 5V/VIN,3V3,GND. Các dây nguồn dài được ẩn về mặt hiển thị (màu rỗng), vẫn giữ nguyên endpoint điện; nhãn nguồn không phải linh kiện điện mới. Tín hiệu giữ màu camADC,xanh dươngDHT,xanh láđiều khiển/PWM,tímI2C; hộp legend giải thích cả màu nguồn. Fan GPIO25 là tên hiển thị theo yêu cầu, code vẫnVAN. [Đối chiếu bản cuối](evidence/final-readability-verification-2026-10-28.md) xác nhận44cặp chân và thuộc tính điện giữ nguyên. Stop/Start để nạp diagram; không cần build cho thay đổi bố cục. Chưa xác nhận render thực bằng UI.

Bảng đối chiếu sau dọn tuyến dây: [44cặp đầu nối giữ nguyên](evidence/layout-cleanup-verification-2026-10-28.md).
