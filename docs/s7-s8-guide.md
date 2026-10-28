# S7–S8: khung tích hợp và công cụ kiểm thử R7

Theo yêu cầu ngày28/10/2026, model thật sẽ thay sau. Bản này hoàn thiện đường tích hợp và công cụ đếnS8 bằng mock. S5 vẫn hoãn. **Model/metrics thật, camera thực và260lượt nghiệm thu chưa được đánh hoàn thành.**

[Kết quả kiểm chứng guide ngày 28/10/2026](evidence/guide-verification-2026-10-28/README.md): phần mềm và MQTT localhost đã chạy đạt; Wokwi trực tiếp chưa chạy được.

## 1. Kiểm tra firmware

Stop/Start Wokwi để nạp bản đã build. Boot có `S7/S8 R7` và `Firmware: R7-<hash>`. MQTT có `firmware_id` và `boot_id` để phân biệt phiên bản và lần restart. GPIO, sơ đồ, ngưỡng local, timeout vàACK không đổi; default gas10ppm, còi volume0.25.

Chờ `WiFi/MQTT/Sub/UTC: 1/1/1/1`. R7 bắt đầu đồng bộ NTP sau khi Wi-Fi kết nối, với3server. Đây là cải tiến khởi tạo, chưa phải bằng chứng đã sửa mọi lỗi giờ của gateway. UTC0 thì chưa nhậnAI; không bỏ kiểm tra timestamp để nhận bản tin cũ.

Nếu local đang nguy hiểm vì slider cũ, đưa MQADC<1700, LDRADC≥750, DHT28°C/45%, rồi ACK khi an toàn đủ3s.

## 2. Một lệnh kiểm tra phần mềm

Mọi terminal bên dưới đều phải ở thư mục `firmware` (nơi có `platformio.ini`). Workspace `PCCC.code-workspace` đặt sẵn thư mục này cho terminal mới.

Máy hiện tại đã có `.venv/bin/python` và PlatformIO. Nếu clone sang máy mới, cần tạo môi trường Python, cài `tools/requirements-mqtt.txt` và cài PlatformIO trước; các lệnh dưới đây không tự cài chúng.

Terminal tại thư mục `firmware`:

```sh
.venv/bin/python tools/verify_project.py
```

Lệnh này buildESP32, chạy test lõi/parser/fusion, unitPython và scenario host. Report/log/hash lưu trong `runs/checks-<UTC>/`. Nó không chạy Wokwi/camera/model và không sửa bảng nghiệm thu.

[Báo cáo kiểm tra đã chạy](evidence/s7s8-final-checks-2026-10-28/report.json): build, host,11unitPython và PC-broker smoke đềuPASS. Bộ scenario host có240PASS/0FAIL/20DEFERRED; số này không phải240lượt Wokwi đạt.

## 3. Thu log và gửi replay

Trước khi chạy: Wokwi phải ở `NORMAL`, `Local/AI: 0/0`, mạng `1/1/1/1`, DHT đọc hợp lệ và không có chương trình khác đang gửi AI vào cùng topic. Host/port/prefix của hai công cụ phải khớp cấu hình ESP32; mặc định là `broker.hivemq.com:1883`, prefix `ptit/nhom07/lab-7c49e2`.

Terminal A, thu 60 giây:

```sh
.venv/bin/python tools/capture_mqtt.py --out runs/s8-demo-01.jsonl --duration 60
```

Chờ `[CAPTURE ready]`. Dòng này chỉ xác nhận PC đã subscribe, chưa chứng minh ESP32 có gửi dữ liệu. Kiểm tra capture có bản tin thiết bị đúng `firmware_id` và `boot_id`.

Terminal B, dùng khoảng cách 5 giây để có thời gian quan sát từng trạng thái:

```sh
.venv/bin/python tools/ai_publish.py --backend replay --interval 5
```

Replay gửi bình thường→khói→lửa→unknown→bình thường. Đây là kết quả viết sẵn, không đọc ảnh. Có thể kích còi/tải/cửa khi ESP đã kết nối và có UTC hợp lệ. Unknown không phát bản tin bình thường. Hết nguồn dữ liệu không tự resetFSM; nếu vàoRECOVERY vẫn cần local an toàn3s vàACK mới.

Đối chiếu theo bảng sau. Mốc thời gian tính từ khi publisher bắt đầu phát, có thể lệch do mạng/mô phỏng; dùng EVENT trong log để kết luận, vì log định kỳ có thể bỏ lỡ trạng thái ngắn.

| Mốc gần đúng | Replay phát | Khi local luôn an toàn, mong đợi trên ESP32 |
|---|---|---|
| 0 giây | `binh_thuong` | `NORMAL`; bơm/van/còi tắt, cửa đóng |
| 5 giây | `khoi` | `WARNING`, AI mức 1; còi bật, bơm/van tắt, cửa vẫn đóng |
| 10 giây | `lua` | `FIRE_SUPPRESSION`, AI mức 2; còi và bơm/van bật, lệnh cửa mở 90° |
| 15 giây | `null` (unknown) | Publisher báo `UNAVAILABLE`, không gửi MQTT. Bản tin lửa trước vẫn còn TTL, không được lập tức coi là an toàn |
| 20 giây | `binh_thuong` | `RECOVERY`; bơm/van/còi tắt, đèn đỏ và cửa mở được giữ |
| Sau khi mức 0 đủ 3 giây | Thả rồi nhấn ACK mới | Về `NORMAL`, xóa chốt, đèn xanh bật, lệnh cửa đóng 0° |

Ở lần chạy sạch, publisher có **4 dòng `PUBACK` + 1 dòng `UNAVAILABLE`**. Bộ đếm ESP `Nhan`/`ai_accepted` phải tăng 4 nếu nhận đủ bản tin hợp lệ, không rớt mạng và không có nguồn phát khác. `PUBACK` riêng lẻ chỉ chứng minh broker xác nhận, không chứng minh ESP đã nhận. Nếu local còn mức 1/2, kết quả sẽ khác bảng vì hệ thống lấy mức cao hơn giữa local và AI.

Đọc capture và trạng thái bảng nghiệm thu:

```sh
.venv/bin/python tools/s8_track.py capture-summary --capture runs/s8-demo-01.jsonl
.venv/bin/python tools/s8_track.py status
```

Dùng tên capture mới cho mỗi lượt; chương trình từ chối ghi đè. Có thể thêm `--expected-firmware-id` với mã từboot để phát hiện thu nhầm phiên bản. Capture lưu UTC/monotonic, topic, QoS/retained, firmware/boot identity và backend do người thao tác khai báo. Summary kiểm tra một số mâu thuẫn dữ liệu, **không tự đánhPASS**. Log lệnh mở cửa chưa chứng minh servo đã quay; phải đối chiếu ảnh/quan sát.

Nếu không thấy kết quả mong đợi:

| Dấu hiệu | Kiểm tra tiếp |
|---|---|
| `UTC: 0` | Chưa đồng bộ giờ; dừng lượt test, giữ log boot và mạng để chẩn đoán |
| Capture không có dòng `device` | ESP đang chạy, MQTT/prefix đúng, đã subscribe và đúng phiên bản firmware chưa |
| PC có `PUBACK`, ESP không tăng `Nhan` | Xem `Ly do goi cuoi`, bộ đếm lỗi/drop, prefix và cờ Sub/UTC; không kết luận đạt |
| Có lệnh `MO` nhưng servo không quay | Đối chiếu hình/quan sát servo và dây/PWM; log chỉ là lệnh |
| Không về `NORMAL` | Cả local/AI phải về 0 đủ 3 giây, sau đó thả rồi nhấn ACK mới |
| Báo file đã tồn tại | Đổi tên capture cho lượt mới, không ghi đè bằng chứng cũ |

## 4. Thay model thật sau bằng plugin

| Thành phần | Hiện tại |
|---|---|
| `ai_adapter.py` | Chuẩn hóa nhãn/confidence, kiểm tra dữ liệu, tạo contract4trườngS6 |
| Replay | Chạy không cần camera/Torch, ghi rõREPLAY_MOCK |
| Plugin | Nhận frameBGR, trảPrediction hoặcNone; chưa có model đi kèm |
| Detector helper | Fire ưu tiênSmoke khi vượt ngưỡng; khôngbox→unknown |
| Model manifest | Mẫu weights/hash/license/preprocessing/dataset/metrics, chưa điền số giả |

Không cài/trainTorch hoặc tải weights trong lượt này. Khi có model, tạo module riêng, ví dụ `my_fire_model.py`:

```python
# Nạp model/weights một lần tại đây, đặt chế độ inference.
def predict(frame_bgr):
    # Đổi màu, resize và chuẩn hóa theo đúng weights.
    # Chạy model; trả label/confidence bằng kiểu Python gốc.
    # Tensor confidence cần chuyển bằng .item().
    # Trả None khi không khả dụng hoặc chưa đủ kết luận.
    raise NotImplementedError("Model chưa tích hợp")
```

`tools/examples/model_plugin.example.py` chỉ là mẫu giao diện; sẽ báo lỗi nếu chưa triển khai. File `.pt` không có cách nạp chung cho mọi kiến trúc. Khi chọn model phải điền `model-manifest.template.json` bằng thông tin thật, gồm weights hash và đánh giá độc lập.

Sau khi có module và dependency model tương ứng:

```sh
.venv/bin/python -m pip install -r tools/requirements-camera.txt
.venv/bin/python tools/ai_publish.py --backend plugin --plugin my_fire_model:predict --source 0 --model-id actual-model-version
```

Module được tìm trong thư mục hiện tại hoặc `--plugin-path`. Source0 là webcam; có thể thay bằng đường dẫnvideo. Camera lỗi, stream kết thúc, exception, NaN, nhãn sai hoặc inference mất≥15s đều không được biến thành bình thường. Publish dùng thời điểm đọc frame vàretain=false. Logplugin ghiPLUGIN_UNVERIFIED vì chạy được plugin chưa chứng minh model đã được đánh giá.

Backend video/camera chưa thử với thiết bị thật. Thời điểm đọc frame không chứng minh ảnh không bị trễ trong bộ đệm camera; tốc độ đọc, buffering và latency phải đo khi có model. Không tuyên bố xử lý realtime từ bộ replay.

Classifier chỉ trả bình thường nếu model đã học nhãn đó. Detector không tìm thấybox không chứng minh cảnh an toàn. Helper chỉ chọn Fire/Smoke vượt ngưỡng, ưu tiênFire nếu có cả hai; không kết quả→None. Chưa thêm temporalfilter hay chính sách nến/bật lửa chưa được kiểm định. Confidence không tự là xác suất cháy thực.

## 5. Phân biệt các miền kiểm chứng

| Miền | Bằng chứng hiện có | Giới hạn |
|---|---|---|
| Host core | Chạy C++FSM/parser thật, đồng hồ/dữ liệu giả | Không chứng minh timingMCU hoặc cơ khí |
| PC-broker smoke | Broker localhost thật; replay/capture gửi nhận được | Devicepayload là PCfixture ghiFAKE_DEVICE_TEST |
| Wokwi | Cần thay đầu vào và quan sát | Còn các ca mạng/latency vàS5 chưa chạy đủ |
| AI thật | Hoãn | Chưa có weights/train/metrics/ảnh dễ nhầm |
| Nghiệm thu260lượt | Bảng gốc vẫnNOT_RUN | Không tự chuyển kết quảhost/mock vào bảng này |

Bộ host có13TC×20hàng gắnHOST_SYNTHETIC. TC01–TC10/TC12/TC13 chạy20biến thể mỗiTC; TC11 để20hàngDEFERRED vì cần ảnh/model thật. Timeout dùngvirtualmillis; có kiểm tra rollover. Đây là regression logic, không phải260lượt nghiệm thu và không phải metrics model.

Khi nghiệm thu cần đủ: nền, MQwarning/danger/biên, LDRgiả lửa, tăng nhiệt, AI thật, mấtAI/TTL, payloadlỗi, AI normal/local danger, ảnh dễ nhầm, timeout vàACK. Ma trận13TC nằm trong [KB](KB.md#s8). Host TC05 chỉ kiểm tra luật nhậnrate; thay nhiệt và lịch đọcDHT cần kiểm chứng riêng trênMCU.

S5 và các ca boot không mạng, reconnect, flood, thời gian đáp ứng, DHT lỗi và servo/còi đồng thời vẫn phải quay lại thử. Maxloopgap trênlog là thời gian giữa vòngloop, không phải latency vật lý của cảm biến.

## 6. Một bảng nghiệm thu gốc, có audit

Bảng gốc là `../tests/integration-results.csv` tính từ thư mụcfirmware. Tool dùng bảng đó làmdefault; có `--ledger` khi chuyển có kiểm soát ởS9. Không tạo bảngPASS song song. Bảng gốc chưa bị thay đổi trong lượt triển khai này.

Capture thô trong `runs/` được Gitignore. Khi chọn minh chứng chính thức, chép log/ảnh cần giữ vào `docs/evidence/`, rồi record bằng đường dẫn đó; không để gói nộp chỉ tham chiếu file thô chưa được lưu cùng dự án. Ghi đường dẫn ảnh bổ sung trongnotes nếu log là minh chứng chính.

Sau một lượt thực, thay phiên bản/tênfile/quan sát trong ví dụ sau bằng dữ liệu thật:

```sh
.venv/bin/python tools/s8_track.py record --scenario TC02 --run 1 --status PASS --domain WOKWI --firmware "R7-HASH_TU_BOOT" --model NONE --evidence docs/evidence/mq-warning-01.jsonl --observed "WARNING; coi bat; tai tat; cua dong"
```

MỗiTC cần20lượt và ít nhất1ảnh/TC. Cófail thì ghiFAIL, phân tích và chạy lại phần ảnh hưởng. Không đặt sốpass để đạt tỉ lệ. CaptureJSONL cần identity khớp và không chứaPCfixture để ghiPASS. Bằng chứng ảnh/logtext vẫn là quan sát của người thao tác; công cụ không chứng thực sự thật vật lý.

Tool không nhận domainHOST/MOCK vào bảng nghiệm thu và không cho ca phụ thuộcmodelPASS vớiMOCK/NONE/UNVERIFIED. Nó dùngfilelock, thayCSVatomic vàauditbefore/after/hash tại `docs/evidence/acceptance-audit`. PUBACK không tự chứng minh ESP đã nhận hay chấp hành đúng.

## 7. Kiểm tra thêm

Thử adapter không gửi MQTT:

```sh
.venv/bin/python tools/ai_publish.py --dry-run --interval 0.1
```

Broker smoke tùy chọn cầnPython≥3.10 và các gói test riêng:

```sh
.venv/bin/python -m pip install -r tools/requirements-test-mqtt.txt
.venv/bin/python tools/verify_project.py --broker-smoke
```

Broker này chỉ bind127.0.0.1, tự chọnport và dừng sautest. Report ghi domain, modelDEFERRED, firmware hash và bảng260lượt có đổi hay không. Chưa mở camera thật, chạy model, đo metrics hoặc điều khiển Wokwi tự động.

Nguồn API: [PlatformIO scripts](https://docs.platformio.org/en/latest/scripting/actions.html), [OpenCV video/camera](https://docs.opencv.org/4.x/dd/d43/tutorial_py_video_display.html). ContractAI v1 giữ như [S6](reference/s6-mqtt-contract.md).
