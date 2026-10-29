# Điểm bắt đầu nghiệm thu bản tích hợp

Theo yêu cầu28/10/2026: triển khai phần mềm còn lại trước; **Word để sau khi nghiệm thu**, không sửa trước hoặc điền kết quả giả. Dashboard, observer/plugin, clockmapper, capture/tracker và công cụ đánh giá/train/đóng gói là các công cụ; có công cụ không đồng nghĩa đã nghiệm thu.

## 1. Thứ tự chạy hệ thống

1. Khởi động broker theo [hướng dẫn local](local-setup.md), build rồi Stop/Start Wokwi. Lấy firmware ID hiện tại từ log boot; các ID trong bằng chứng ngày28/10 là lịch sử, không dùng làm ID cho build mới.
2. Chạy [dashboard](dashboard.md); app tự kết nối theo `.env`. Kiểm tra ESP trực tiếp/lịch sử riêng với kết nối broker.
3. Đưa local về nền, ACK hợp lệ để NORMAL. Chờ mạng1/1/1/1.
4. Thu capture ở terminal A và publisher ở terminal B **đồng thời**, theo [Wokwi clock](wokwi-clock.md). Dùng tênfile mới. Model thật dùng capture `--ai-backend MODEL_UNVERIFIED` cho tới khi đánh giá đủ; không tự khai REAL_MODEL chỉ để tool cho PASS.
5. Thực hiện ca thử, ghi expected/observed, firmware/model, clockdomain, input và output, ảnh/log. Dùng đồng hồ môphỏng cho các mốc60s/3s và ghi rõ giới hạn khi đo walltime.
6. Sau mỗi lượt đưa về nền và ACK; không để state/timeout của lượt trước làm sai lượt sau.

## 2. Ma trận13ca — mỗi ca20lượt

Bảng gốc duy nhất: `../tests/integration-results.csv`. Input chi tiết phải đối chiếu tài liệu thầy/KB trước khi ghi kết quả chính thức. Bảng sau là trình tự thao tác theo code hiện tại, không thay đổi điều kiện nghiệm thu gốc.

| TC | Thao tác chính | Điều cần đối chiếu |
|---|---|---|
| TC01 | Local nền, nguồn AI theo phạm vi đã đánh giá | NORMAL, xanh bật, tải/còi tắt, cửa đóng; không nhầm unknown thành normal |
| TC02 | MQ đi qua1800 ADC, rồi về<1700 | WARNING, còi/đỏ bật, tải tắt, không tự mở cửa trước FIRE |
| TC03 | MQ≥2800 ADC, rồi về<2700/<1700 | FIRE,2relay+tải, cửa mở; RECOVERY vàACK |
| TC04 | LDR ADC≤500 rồi≥750 | Lửa giả, nguồnLOCAL, FIRE rồiRECOVERY; không gọi LDR làIR |
| TC05 | DHT tăng nhiệt nhanh theo mẫu3s; thử riêng55°C vàrate2°C/s | Phân biệt ngưỡng tuyệt đối/rate; mẫu đầu/lỗi xen giữa không giảrate0 |
| TC06 | Local nền, model thật phátlửa đủđiềukiện | SourceAI, ESPaccepted tăng, FIRE/tải/cửa; mock chỉ dùng diễn tập |
| TC07 | MQ quanh1800/1700 và2800/2700 | Hysteresis: không rungstate, đúng biên so sánh |
| TC08 | Dừng AI/đứtMQTT | AIhếtTTL15s, không refresh bởi gói lỗi; local độc lập; đừng đồng nhất TTLmôphỏng vớiwalltime |
| TC09 | Gửi JSON/type/field/confidence/size/timestamp/duplicate lỗi | Reject/drop đúng, không gia hạn AI hợp lệ, không làm đứnglocal |
| TC10 | Local nguyhiểm + AInormal | Local vẫn giữmức2, tải hoạtđộng theoFSM |
| TC11 | Ảnh khó: tóc/đỏ/nến/hơi nước/che khuất | Kết quả thật, confidence, báo giả/bỏsót; không đặt sốaccuracy giả |
| TC12 | Giữ nguyhiểm60s, giữthêm10s | Bơm/van tắt, khóa táikích, cửa giữmở; nền+ACKmới mới rearm |
| TC13 | ACKkhi nguyhiểm/giữnút/nhấnsớm; nền3s rồi nhấnmới | Không resettráiđiềukiện; đúngNORMAL/cuốiđóngcửa |

Các ca bổ sungS5/S6: bootkhôngWiFi/broker, mấtmạngkhiFIRE, reconnect+subscribe, nguồnđồngthời, servo+còi, lỗiDHTsau nguyhiểm, đo loopgap vàlatencyvới phươngpháp đãghi. Ca lỗiDHTruntime cần gây mất mẫu khi đang chạy; nếu simulator không cho thay dây sống, không dùng reboot rồi tuyên bố đã thử giữ nguyhiểm qua lỗi. Hostregression chỉ là bằngchứng code, ghi BLOCKED cho runtime chưa tạođược điềukiện và nêu cách thử phầncứng/diagnostic riêng.

## 3. Công cụ gửi ca mạng

```sh
.venv/bin/python tools/network_cases.py --case future --wokwi-clock --expected-firmware-id "FIRMWARE_ID_TU_LOG_BOOT"
```

Thay `FIRMWARE_ID_TU_LOG_BOOT` bằng ID thật trong log boot. Đổi case thành `old`, `duplicate`, `json`, `missing`, `type`, `confidence`, `oversize`. Đây là dữ liệu test protocol, không phải model thật. `flood --count 32` phát burst có giới hạn; xemdrop/loopgap/local, không mặc định kếtluận đãđạt.

Retained: `--case retained`, reconnectESP trongTTL để xemrejectdelivery, sauđó **xóa bằng `--case clear-retained`**. MQTT3.1.1 có thể chuyển live retainedpublish với retain=false nên chỉ gửi retain=true lúcđangsubscribe chưa đủ kiểmchứng retainedreject. Clockmapper bindboot; restartESP thì chạy lạipublisher. Các ca mấtmạng/chậm/flood phải thu log và quan sátactual, không tự chạy cácprobe lên broker khi chỉ mở dashboard.

## 4. Ghi kết quả và khuyết điểm

Chép bằngchứng đãchọn vào docs/evidence rồi dùng `s8_track.py record` theo [guide](s7-s8-guide.md#6-một-bảng-nghiệm-thu-gốc-có-audit). MỗiTC ít nhất1ảnh và20lượt. Loglệnh không chứngminh chuyểnđộng cơkhí/tiếpđiểm; quan sát tải/cửa/còi thực trongsimulator. FAIL phải được ghi và sửa; không dùng tỉlệ18/20 che lỗi bắtbuộc. Bảng vẫnNOT_RUN tới khi có lượt thực được ghi.

## 5. AI còn thiếu dữ liệu

Nhóm xác nhận **chưa có dataset gán nhãn**. Có [công cụ audit/evaluate/train](ai-evaluation.md), không chạytrain hoặc tạo metrics khi chưa có dữliệu. YOLOdetector2lớp fire/smoke khác classifier3lớp của khung banđầu; cần thốngnhất phạmvi này trước khi viết báo cáo. Khôngbox làunknown, không phải bằngchứng bìnhthường. Ảnh200/lớp, tập độc lập và mAP/recall/báogiả chưa thể coi hoànthành từ những ảnhđãthử.

Temporalfilter đã có dạng opt-in3frame/2s (wallclockPC), maxgap5s; không bật cho rawdiagnostic/replay và chưa được hiệu chỉnh bằngdataset. Nó giảm sự kiện thoángqua, không chữa nhậnnhầm kéo dài; confidence vẫnnguyênbản, no detection không phátnormal. Xem lệnh trong guideAI.

## 6. Chuẩn bị gói nộp sau nghiệm thu

```sh
.venv/bin/python tools/package_submission.py --out runs/pccc-review-01.zip --include-weights
```

Đây là gói review, gồm source/dashboard/tools/docs/minhchứng và bản sao duy nhất ledger tại acceptance/integration-results.csv. Không cósecrets/runs/venv/.pio. Word chưa sửa/chưa kèm. Sau nghiệmthu, thêm `--report /duong/dan/bao-cao.docx`; kiểmtra manifest/license/dataset và yêucầunộp trước khi gửi. Công cụ không publishrepo hoặc tạo linkWokwi côngkhai.
