# KB thiết kế triển khai và checklist Nhóm 07

Cập nhật 28/10/2026, theo trao đổi trực tiếp với người dùng. Đây là **KB duy nhất để theo dõi quyết định, đề xuất, chênh lệch ba bên, thứ tự triển khai và checklist**. Các tài liệu khác chứa giải thích, hướng dẫn thao tác hoặc bằng chứng; trạng thái tiến độ mới được cập nhật tại đây. Phân biệt quyết định đã thống nhất với chức năng đã triển khai; không dùng tài liệu này làm bằng chứng test pass. **S2–S4 đã có R5; S5 hoãn theo người dùng. R6 thêm S6 MQTT/contract/mock, build/host/PC-broker smoke pass, chưa nghiệm thu runtime Wokwi. DOCX chưa sửa.**

<a id="progress"></a>

[Mở bản đồ thư mục và điểm bắt đầu](project-map.md) · [Hướng dẫn hiện tại](s7-s8-guide.md)

[Dashboard local](dashboard.md) · [Bản chuẩn bị nghiệm thu](acceptance-ready.md) · [Dữ liệu và đánh giá AI](ai-evaluation.md)

## Tiến độ S0–S9 — bắt đầu tại đây

**Đã triển khai phần mềm tới S8 theo chế độ mock; cập nhật mới nhất có model YOLOv8n và observer chạy local, chưa nghiệm thu model→MQTT→ESP.** S5 vẫnHOÃN. S6 có mạng/contract/fusion; S7 có adapter/replay/plugin để thay model sau; S8 có regression, capture và công cụ quản lý bảng nghiệm thu. Build/host/unit/PC-broker smokePASS. **Chưa hoàn tất nghiệm thu S8:** còn lượtWokwi/ảnh, model/metrics thật và các phép đo mạng/latency trênMCU. Không lấy kết quảmock làm kết quảmodel.

| Bước | Nội dung | Trạng thái hiện tại | Checklist chi tiết |
|---|---|---|---|
| S0 | Ôn GPIO, ADC, PWM và flow chương trình | Đã đi một vòng giải thích; ôn tiếp khi cần, phần tự diễn giải chưa xác nhận | [H01–H06](#s0) |
| S1 | Chốt board, LDR, hai relay, servo, DHT/ACK | Đã chốt thiết kế local | [P01–P06](#s1) |
| S2 | Giữ nguy hiểm nhiệt khi DHT lỗi | Đã code; build/host tests pass, runtime lỗi DHT còn trong S5 | [I01–I07](#s2-s4) |
| S3 | LDR demo lửa | Đã code; người dùng đã thấy sáng tăng→ADC<500→còi | [I01–I07](#s2-s4) |
| S4 | Servo cửa + hai relay | Đã code; đã thấy LED tải sáng và xác nhận đóng cửa; toàn bộ state chờ S5 | [I01–I07](#s2-s4) |
| S5 | Kiểm chứng local trong Wokwi | **HOÃN theo người dùng**, chưa đóng L01–L10 | [L01–L10](#s5) |
| S6 | MQTT, contract, TTL, mock | Có code/test và trace replay PC→ESP nhận4gói/chuyểnFSM sau clockmapper; model đã PUBACK. Reconnect/flood/latency đầy đủ còn chờ | [N01–N08](#s6) |
| S7 | Adapter/publisher AI + model | **Khung R7 đã có; YOLOv8n pretrained đã nạp/thử ảnh và webcam; có observer/plugin. Đánh giá, lọc thời gian và tích hợp model→MQTT→ESP chưa hoàn tất.** | [M01–M10](#s7) |
| **S8** | **Công cụ kiểm thử và nghiệm thu** | **Tooling đã có; host240PASS/20DEFERRED; bảng260lượt thực vẫnNOT_RUN** | **[E01–E08 và13TC](#s8)** |
| S9 | Đồng bộ báo cáo và đóng gói | Chưa sửa DOCX | [R01–R09](#s9) |

**Việc tiếp theo:** Stop/Start bảnR7, dùng [hướng dẫn S7–S8](s7-s8-guide.md) để thu log và thử replay; `tools/verify_project.py` chạy các kiểm tra phần mềm bằng một lệnh. Các phần model thật giữ hoãn để thay sau, không cản việc chuẩn bị/test tích hợp bằngmock.

Mốc local đã commit: `a730740` (layout + gas10ppm + volume0.25). Phần S6–S8/R7 đã được commit theo nhóm chức năng; xem git log. Các bước AI local và clock mapper được ghi ở nhật ký phía dưới. [Hướng dẫn hiện tại S7–S8](s7-s8-guide.md); [contract S6](reference/s6-mqtt-contract.md).

## Cách đọc và điểm bắt đầu

- **Đã chốt:** người dùng đã đồng ý hướng thiết kế. Không đồng nghĩa đã code hoặc test.
- **Đề xuất:** khuyến nghị của Codex, chưa coi là lựa chọn được nhóm chốt.
- **Có code:** tìm thấy triển khai; chỉ ghi đã kiểm chứng khi có log/ảnh/test và đúng phiên bản.
- **Chờ làm / chờ test:** chưa có kết quả đủ để đóng việc. Ô `[x]` chỉ đánh khi đạt điều kiện và có bằng chứng; không tự đổi NOT_RUN thành PASS.
- P0: cần trước khi chốt nhánh local hoặc trước tích hợp phụ thuộc; P1: bắt buộc cho nghiệm thu cuối; P2: mở rộng tùy chọn.
- Bằng chứng có ở bản nút giả lửa không tự chứng minh bản LDR/servo sau thay đổi. Mỗi lần sửa ghi các test cần chạy lại.

**Điểm tiếp theo:** kiểm tra tích hợp R7 bằng mock và ghi log theo [S7–S8](s7-s8-guide.md). S5/model thật hoãn; S9 chưa bắt đầu.

| Theo dõi nhanh | Trạng thái 28/10/2026 |
|---|---|
| Firmware hiện tại | R7 có local + MQTT/fusion + identity; GPIO/ngưỡng/FSM/tải không đổi trong bước S7–S8; S5 hoãn |
| Lỗi quan trọng | A16 đã có regression fail trước sửa/pass sau sửa; giữ nhiệt cao/rate qua DHT lỗi hoặc stale; timeout vẫn dừng tải |
| Thiết kế mới được đồng ý | LDR demo lửa; hai relay bơm/van + servo cửa; DHT3 s |
| Lựa chọn kỹ thuật | Đã chọn LDR32/100ms/ADC500-750 và servo33/0-90°/50Hz kênh8; cần kiểm chứng runtime. MQTT/schema đã chọnR6; task modelAI thật chưa chốt. |
| AI/MQTT/dashboard | MQTT có log ESP→PC; adapter/replay/plugin R7 sẵn; chưa có model thật/dashboard |
| Báo cáo | Đã review, chưa sửa DOCX; còn mâu thuẫn và phần mẫu chưa điền |
| Nghiệm thu đầy đủ | Chưa thực hiện đủ 13×20 lượt; không tính host tests thay integration |

## Bảng quyết định hiện tại

| ID | Hạng mục | Quyết định hoặc trạng thái | Vì sao | Đã triển khai? |
|---|---|---|---|---|
| D01 | Board | **Đã chốt DOIT ESP32 DevKit V1** ngày27/10/2026 cho thiết kế hiện tại; đồng bộ báo cáo sang V1. Không suy ra yêu cầu mua phần cứng. | Mạch Wokwi và PlatformIO đều là V1; đủ GPIO và các chức năng đang cần. V1 DOIT và DevKitC V4 Espressif là hai thiết kế board, không phải cùng một dòng nâng cấp chip từ đời 1 lên đời 4. | V1 đang dùng; DOCX còn ghi V4, chưa sửa. |
| D02 | MQ-2 | Tiếp tục MQ-2 mô phỏng, đọc analog. Giá trị firmware hiện là ADC, chưa quy đổi ppm. | Wokwi có MQ-2; không cần thay biến trở vì cho rằng thiếu linh kiện. Cần phân biệt nồng độ nhập trong simulator với số ADC firmware đọc được. | Có MQ AOUT→GPIO35; ngưỡng ADC cần test lại trên mạch hiện tại. |
| D03 | Demo phát hiện lửa | **Đã chốt LDR đọc analog; ánh sáng tăng đủ mạnh là sự kiện lửa giả lập**, thay vai trò demo lửa của nút đỏ hiện tại. Chọn ngưỡng/hysteresis sau khảo sát. | Người dùng muốn khôi phục demo thay đổi ánh sáng như đồ án IoT cũ, thay vì chỉ bấm nút tạo tín hiệu có/không. | **Đã code/diagram R5:** LDR AO→GPIO32,100ms, ADC≤500 kích/≥750 giải trừ; chờ S5. |
| D04 | Bơm và van | **Giữ hai relay riêng cho bơm và van.** | Giữ chức năng và tình huống TC03 trong hướng dẫn; cửa thoát hiểm không thay thế chức năng van. Người dùng đồng ý đề nghị này. | Có code/diagram hai relay; còn cần bằng chứng runtime. |
| D05 | Cửa thoát hiểm | **Bổ sung servo cửa, cùng tồn tại với hai relay. Đã chốt: mở khi FIRE, giữ mở ở RECOVERY, đóng sau ACK an toàn hợp lệ.** Boot chưa có nguy hiểm/NORMAL/WARNING trước FIRE thì đóng. | Khôi phục chức năng demo cửa mà nhóm mong muốn, không loại bỏ điều khiển van. | **Đã code/diagram R5:** PWM33,0/90°,50Hz16bit/kênh8 khác group còi; chờ quan sát S5. |
| D06 | DHT22 | **Giữ lịch đọc riêng 3 giây.** | Phù hợp lịch riêng khuyến nghị của hướng dẫn và code; không gom DHT vào chu kỳ 1 giây của MQ. Người dùng đã đồng ý. | Có code lịch 3 s. |
| D07 | AI | **Ghi nhận để làm sau; chưa chốt classifier hay detector.** | Cần hiểu và kiểm chứng nhánh cục bộ trước. Báo cáo đang trộn classifier ba lớp với YOLO detector hai loại đối tượng; chưa đủ cơ sở ép chọn một hướng. | Chưa có pipeline AI/MQTT trong firmware hiện tại. |
| D08 | Mất DHT sau nguy hiểm nhiệt | **Đã chốt giữ nguyên nhân nguy hiểm cho tới mẫu hợp lệ xác nhận giải trừ; vẫn giới hạn bơm60s.** | Mất số đo không có nghĩa nhiệt đã giảm; không cho bơm vô hạn. | **Đã sửa R5 và regression pass**; còn test runtime nếu ngắt DATA trong cùng lượt chạy được. |

## D08 DHT mất dữ liệu sau nguy hiểm nhiệt

**Đã được người dùng chốt ngày27/10/2026.** Khi nhiệt cao hoặc tốc độ tăng nhiệt hợp lệ đã kích nguy hiểm, lần đọc DHT lỗi/già không chứng minh điều kiện đó đã hết. Giữ nguyên nhân nguy hiểm đã xác nhận cho đến mẫu hợp lệ chứng minh hết điều kiện tương ứng. Luật khói/LDR vẫn độc lập; không bỏ qua nguy hiểm của nguồn khác.

Hạn bơm60s và khóa timeout vẫn ưu tiên theo FSM. Đến hạn thì dừng bơm/van, giữ RECOVERY và cửa mở; không xóa nguyên nhân nhiệt chỉ vì timeout. Chỉ ACK khi dữ liệu/đầu vào đáp ứng điều kiện an toàn3s và có lần nhấn mới. DHT lỗi khi chưa từng có nguy hiểm nhiệt vẫn xử lý cảnh báo theo chính sách hiện có. Đã sửa trong R5: tách chốt nhiệt tuyệt đối/rate, chỉ mẫu hợp lệ giải trừ; rate NaN sau lỗi không xóa chốt rate. `thermalUnconfirmed` có trên log/CSV. Regression failed/stale/timeout pass, runtime chưa xác nhận.

## D03 Demo LDR và giới hạn cần giữ rõ

LDR là cảm biến ánh sáng, không phải cảm biến lửa hồng ngoại. Demo thay đổi độ sáng để tạo đầu vào cho luật phát hiện lửa chỉ chứng minh cách thu nhận tín hiệu và phản ứng của chương trình; không chứng minh độ nhạy hoặc khả năng phân biệt lửa thật.

Khi triển khai cần làm đồng bộ:

1. Đã chốt đọc analog; chọn linh kiện và chân ADC1 còn trống để tương thích kế hoạch Wi-Fi. R5 đã gán GPIO32; wiring được kiểm tra tĩnh, runtime còn chờ.
2. Đã chốt ánh sáng tăng đủ mạnh là sự kiện giả lập lửa. Chọn ngưỡng và hysteresis từ phép thử mô phỏng; ban đầu log ADC, không mặc định ánh sáng tăng làm số ADC tăng vì còn phụ thuộc cách mắc linh kiện.
3. Chuyển đầu vào LDR thành tín hiệu phát hiện lửa đưa vào luật/FSM; quyết định có cần thêm trường giá trị ánh sáng và trạng thái hợp lệ trong SensorSnapshot.
4. Cập nhật diagram, config, sensors, log/LCD, kiểm tra wiring và hướng dẫn test. Nút ACK vẫn giữ vai trò riêng, không bị thay bởi LDR.
5. Sửa báo cáo để mô tả LDR là phương án mô phỏng ánh sáng thay cho cảm biến lửa; không gọi phép đo lux là phép đo nguy cơ cháy đã hiệu chuẩn.

Không sao chép nguyên GPIO35 của LDR từ IoT cũ: chân này hiện dành cho MQ-2. Nếu giữ nút đỏ như công cụ test phụ thì phải ghi rõ vai trò phụ, không tiếp tục mô tả nó là đầu vào demo lửa chính.

## D04 và D05 Hai relay và servo cửa

Thiết kế đích được đồng ý:

```text
ESP32 → relay bơm
      → relay van
      → servo mô phỏng cửa thoát hiểm
```

Đã chốt hành vi trong S1 ngày27/10/2026: mở khi vào FIRE_SUPPRESSION, giữ mở qua RECOVERY (kể cả timeout); chỉ đóng khi mọi đầu vào đủ điều kiện an toàn3s và có cạnh ACK mới hợp lệ. Boot chưa phát hiện nguy hiểm, NORMAL và WARNING trước FIRE thì đóng. Nhấn ACK khi còn nguy hiểm không đóng cửa. R5 dùng GPIO33,0°/90°,50Hz16bit,500us/1500us; kiểm tra core2.0.17 xác nhận kênh8/group1 không chung timer với còi kênh0/group0. Người dùng đã xác nhận đóng cửa trên Wokwi ngày28/10; chuỗi góc mở/đóng đầy đủ và phép đo thực còn theo S5.

Kiểm tra GPIO và kênh PWM với còi LEDC hiện tại; không chép GPIO19 của servo IoT cũ vì đang dùng cho ACK. Thêm test riêng servo và test đồng thời bơm/van/còi/cửa. Đây là cửa mô hình học thuật, chưa phải thiết kế cơ cấu thoát hiểm thực tế.

### Bảng đầu ra thiết kế đích đã chốt

| Trạng thái/tình huống | Bơm/van | Cửa servo | Còi | Đỏ | Xanh |
|---|---|---|---|---|---|
| Boot chưa phát hiện nguy hiểm / NORMAL | Tắt | Đóng | Tắt | Tắt | Bật khi đã ở NORMAL |
| WARNING trước FIRE | Tắt | Đóng | Bật | Bật | Tắt |
| FIRE_SUPPRESSION | Bật | Mở | Bật | Bật | Tắt |
| RECOVERY, kể cả timeout | Tắt | Giữ mở nếu đã mở do FIRE; giữ đóng nếu chỉ WARNING | Tắt | Bật | Tắt |
| ACK hợp lệ sau an toàn3s → NORMAL | Tắt | Đóng | Tắt | Tắt | Bật |

RECOVERY sau WARNING không tự mở cửa vì chưa có FIRE. ACK khi còn nguy hiểm bị bỏ qua. Khi boot phát hiện nguy hiểm, áp dụng state đánh giá được, không giữ đầu ra NORMAL cố định. Trước khi đọc/đánh giá xong, mức điện khởi tạo và thời điểm servo attach cần kiểm tra; bảng không phải bằng chứng cơ khí đã chạy. Các cột là **lệnh** thiết kế, không phải feedback tải.

## D01 Chức năng V4 và lý do chưa chuyển

ESP32-DevKitC V4 đưa các giao tiếp GPIO, ADC, PWM, I2C, SPI và UART ra chân để kết nối cảm biến, màn hình và cơ cấu chấp hành; có USB–UART để nạp firmware/log và Wi-Fi/Bluetooth theo module ESP32. Những nhóm chức năng này cũng có ở board V1 hiện dùng; V4 không tự bổ sung thuật toán AI hay khả năng hiểu lửa.

DevKitC V4 có nhiều biến thể module: bản WROOM và bản WROVER có thể khác bộ nhớ/PSRAM và chân khả dụng. Không mặc định mọi V4 đều có PSRAM, camera hoặc mạnh hơn V1. Nếu sau này có phần cứng cụ thể, tra đúng mã module/board, pinout, nguồn và cấu hình build rồi mới quyết định đổi.

Nguồn: [Espressif DevKitC V4](https://docs.espressif.com/projects/esp-dev-kits/en/latest/esp32/esp32-devkitc/user_guide.html), [PlatformIO DOIT DevKit V1](https://docs.platformio.org/en/latest/boards/espressif32/esp32doit-devkit-v1.html).

## D07 AI để xử lý sau

Giữ nguyên mục tiêu kiến trúc hai nhánh: cảm biến/luật cục bộ trên ESP32; camera/video và AI trên PC; trao đổi bằng MQTT. AI chỉ được nâng mức nguy hiểm, không hạ mức do local xác định. Đây là đích thiết kế, chưa có code tích hợp.

Chưa chốt: classifier ba lớp hay detector Fire/Smoke; dataset; mô hình; quy tắc quy đổi kết quả; schema MQTT; confidence; cách xác nhận nhiều frame; chính sách nến/bật lửa; chỉ tiêu và kết quả đo. Các giá trị trong tài liệu kế hoạch cũ là đề xuất để xem lại, không phải mọi chi tiết đều đã được người dùng phê duyệt.

Khi quay lại AI, kiểm tra sản phẩm thật mà thành viên phụ trách đã có trước khi yêu cầu huấn luyện lại. Detector hai loại đối tượng là một hướng thầy cho phép nâng cao, nhưng cần tầng quyết định và kiểm thử phù hợp; không tự gọi không có detection là cảnh chắc chắn an toàn.

## Việc cần xử lý trước khi chốt nhánh cục bộ

- A16 đã sửa R5 và có regression pass cho nhiệt/rate→failed/stale→phục hồi và timeout. Chưa có bằng chứng ngắt DHT trong cùng lần chạy Wokwi.
- LDR/servo đã triển khai R5 theo thiết kế chốt; cần xác nhận các ngưỡng ADC và chuyển động PWM bằng runtime S5.
- Test runtime từng trạng thái, hai relay, servo, LDR, DHT, ACK và timeout; unit test không thay bằng chứng Wokwi.
- Đồng bộ DOCX: board, LDR, hai relay + servo, bảng chân, sơ đồ, lịch đọc, FSM và TC; không điền kết quả khi chưa chạy thật.

## Ma trận ba bên và việc còn phải sửa

Nguồn T = hướng dẫn thầy, nhất là Phần F. B = báo cáo AutoRecovered. C = code hiện tại. Các định vị §/Bảng dưới đây thuộc B, trừ khi ghi Phần F. Giữ nội dung review gốc ở [bản so sánh](../../docs/review-2026-10-27/three-way-review.md). Để nghiệm thu, theo chức năng đã thống nhất với thầy; cách triển khai phải kiểm chứng bằng tài liệu kỹ thuật và test, không mặc định T/B/C đúng toàn bộ.

| ID | Chênh lệch hoặc concern | Nên theo gì và vì sao | Việc và điều kiện đóng | Trạng thái |
|---|---|---|---|---|
| A01 | B §1.3/2.1/Bảng3.2 ghi V4; T/C dùng V1 | Đã chốt giữ V1 ở S1; V4 không tự nâng cấp khả năng AI | Đồng bộ tên board, pinout, build và ảnh mạch; chỉ đổi board nếu có yêu cầu cụ thể | V1 hiện dùng; B chưa sửa |
| A02 | B §3.2 nói không có MQ nên thay biến trở; Bảng3.2 lại nói MQ có sẵn | Theo mạch MQ hiện dùng và khảo sát Wokwi | Sửa đoạn thiếu MQ; chụp khảo sát và mạch thật | Chưa sửa B |
| A03 | B mô tả dải ppm; C đọc ADC | Giữ ADC khi chưa có phép quy đổi; không nói ADC=ppm | B giải thích chuỗi nồng độ mô phỏng→điện áp→ADC; log không gắn ppm cho ADC; hiệu chuẩn vật lý là việc riêng | C ghi ADC; B cần bổ sung |
| A04 | B mô tả LDR, C đang nút DO | Theo D03 đã chốt demo LDR | Triển khai tín hiệu LDR, ngưỡng/đơn vị/log/test; nêu rõ thay thế tín hiệu, không mô phỏng vật lý IR | Có code/diagram R5; chờ S5 và sửa B |
| A05 | B lẫn relay+servo và hai relay; TC03 cần bơm/van | Theo D04/D05: hai relay + servo bổ sung | Đồng bộ FR, danh mục, bảng chân, flow, chấp hành và TC; không xóa chức năng van | Hai relay+servo có code R5; B và S5 còn chờ |
| A06 | Copy chân IoT cũ gây đụng MQ35/ACK19 | Giữ MQ35/ACK19; phân bổ mới sau kiểm tra | Chốt pinout và PWM, cập nhật static checks; không gán chân mới chỉ theo vị trí vật lý | Chọn LDR32/servo33, wiring/PWM static pass; runtime chờ |
| A07 | B §1.2 gom T=1s, NFR02 DHT riêng; C MQ1s/DHT3s/lửa20ms | Theo T và lịch C, đổi lịch đọc LDR theo thiết kế mới | B có bảng lịch riêng; test khoảng đọc thực; 20ms là lịch danh nghĩa | DHT3s đã chốt; B chưa sửa |
| A08 | B MT01/02<1s, NFR01≤2s nói chung | Đề xuất phân ngân sách theo nguồn và mốc đo | Tách đầu vào đổi/lấy mẫu/quyết định/lệnh/tải; không hứa phản ứng nhiệt<1s mọi lúc với DHT3s; lưu số đo và giới hạn | Chưa đo/chưa sửa |
| A09 | B mới mô tả luật chung; C có ngưỡng/hysteresis | Dùng luật đã kiểm chứng và nêu rõ tham số mô phỏng | B ghi MQ1800/2800, ngưỡng xuống1700/2700, nhiệt55/53, rate2 C/s; cập nhật nếu có thay đổi được giải thích | Có code; runtime còn chờ |
| A10 | T WARNING→RECOVERY cần ACK; C tự sang RECOVERY khi level0, vẫn giữ đỏ | Đề xuất giữ C và mô tả khác biệt: tự sang RECOVERY không phải tự về NORMAL | Vẽ đúng flow và test chỉ ACK hợp lệ mới về NORMAL; nhóm/thầy biết lý do thay đổi | Có code; B/flow chưa điền |
| A11 | C thêm debounce50ms, cạnh mới, an toàn3s | Đề xuất giữ để tránh nút giữ sẵn tự reset | Test bounce/giữ từ boot/nhấn sớm/nhấn khi nguy hiểm; ghi vào B | Có code/host tests; runtime chờ |
| A12 | Khung T warmup MQ trả0 cho mọi nguồn | Theo yêu cầu local độc lập, sửa cách triển khai mẫu | Simulator ghi không warmup; nếu mạch thật thì warmup chỉ nhánh MQ; không dùng20s như chứng minh đã ổn định vật lý | C simulator; hardware chưa làm |
| A13 | Khung T chờ Wi-Fi vô hạn ở setup | Theo yêu cầu local luôn chạy, không theo vòng while mẫu | Boot không mạng vẫn đọc/điều khiển; reconnect không chặn local; đo khi broker timeout | Chờ S6 |
| A14 | Khung T dt sai sau đọc DHT lỗi | C dùng timestamp và reset chuỗi rate sau lỗi | Giữ unit test dt/rollover/lỗi xen giữa; B nêu cần2mẫu tốt liên tiếp để rate trở lại | Có code; cần duy trì khi sửa S2 |
| A15 | Khung T timeout có thể tái kích ngay; C chốt khóa | Theo mục tiêu TC12, giữ khóa của C | Test đủ60s vẫn nguy hiểm thêm10s không tự bật; ghi đây là giới hạn một lượt liên tục, không tự gọi tổng cả sự cố | Có code/host test; runtime chờ |
| A16 | C mất DHT sau nhiệt cao làm dừng bơm, DANGER_CLEARED | Đã chốt D08: không coi mất dữ liệu là bằng chứng nhiệt giảm; vẫn giữ timeout | Chốt chính sách, sửa evaluate/FSM/reason, thêm regression; log trường hợp60C→lỗi không báo đã an toàn | Đã sửa R5, regression pass; chờ runtime |
| A17 | T ví dụ relay LOW; B/C HIGH | Theo module cấu hình, không quy LOW/HIGH là đúng cho mọi relay | Giữ npn explicit; quan sát LED tải COM-NO NORMAL/FIRE/RECOVERY; log lệnh≠feedback | Có wiring; runtime chờ |
| A18 | B active buzzer/HIGH và nháy100/500ms; C passive LEDC2kHz/đỏ steady | Đề xuất giữ C, sửa B nếu không chọn mẫu nháy | Ghi loại còi, phương pháp điều khiển, mẫu LED; kiểm tra không xung đột servo PWM | Chưa đồng bộ B |
| A19 | T/B yêu cầu CSV; C mặc định chữ dễ đọc | Giữ Readable/Csv/Both cho học và lấy bằng chứng | B mô tả2mục đích; thu CSV đúng header/nguồn/EVENT; không tính boot text vào CSV | Có code; thu runtime chờ |
| A20 | T classifier3, B detector2 + FR03 classifier3 | Chờ D07; detection được T cho phép, không ép đổi model có sẵn | Chọn một pipeline, sửa các chương/FR/dataset/metrics; nếu detector phải có tầng quy đổi kết quả | Chưa chốt |
| A21 | B có mục tiêu mAP@0.5≥85%, còn mẫu accuracy/confusion | Theo loại mô hình và phép đo thực | Detector: mAP/P/R, thêm hệ thống; classifier: accuracy/confusion/recall; 85%/80% là mục tiêu chưa đạt; không gọi mAP là tỉ lệ đúng từng ảnh | Chưa có metrics |
| A22 | ≥200ảnh/lớp trong T; detector không có box Normal | Đề xuất vẫn có ảnh nền/khó; điều chỉnh mô tả dataset phù hợp task | Ghi nguồn/license/số ảnh/instance; tách video nguồn tránh leakage; ảnh âm tính không tùy tiện bỏ | Chưa có dữ liệu trong workspace |
| A23 | B khẳng định AI hiểu ngữ cảnh, giảm báo giả, nhận gas | Chỉ giữ khả năng đã thử, giới hạn theo loại camera/task | Không gán cho RGB khả năng đo khí vô hình; nến có Fire thật nhưng quyết định nguy hiểm là policy khác; thêm ảnh nhầm/test và giới hạn | Chờ sửa B/S7 |
| A24 | B gộp cảm biến lửa với đợi khói/nhiệt tới vị trí | Sửa mô tả cơ chế | Nêu cảm biến lửa quang học phụ thuộc tầm nhìn/phổ/nhiễu, không cần khói bay tới; LDR demo không chứng minh IR | Chưa sửa B |
| A25 | B schema timestamp/detections/alarm_level; kế hoạch C v/nhan/do_tin_cay/ts_ms | Đề xuất hợp đồng chung và adapter nếu dùng detector | Chốt topic, label, type, confidence, timestamp/unit, TTL, seq/session, kích thước; alarm_level không vượt quyền local/FSM | Chưa triển khai |
| A26 | T callback mặc định trường thiếu, refresh trước validation | Kiểm tra ngữ nghĩa ngoài JSON syntax | Payload thiếu/sai kiểu/nhãn lạ/confidence không hữu hạn/ngoài[0,1]/quá dài phải xử lý rõ; gói lỗi không gia hạn AI hợp lệ | Chờ S6 |
| A27 | B QoS1 bảo đảm không mất; PubSubClient publishQoS0 | Theo khả năng thư viện/chiều truyền thật | Chốt thư viện/version; phân publish và subscribe, QoS và retained; xử lý duplicate/stale; không tuyên bố bảo đảm tuyệt đối | R6 chốt ESP-MQTT/ESP publish0, mockpublish1/sub1; B chưa sửa |
| A28 | T/B AI chỉ nâng, TTL/reconnect; C chưa có mạng | Theo yêu cầu chức năng thầy | Hợp nhất max(local,AI hợp lệ); TTL/mấtAI/UI, subscribe sau reconnect, hai chiều; mock không thay model thật | R6 có hợp nhất/TTL/mock; chờ MCU runtime/S7model |
| A29 | B Arduino IDE, đã dùng các thư viện mạng | Theo môi trường thật | Ghi VSCode/PlatformIO + Arduino framework và version thực; mạng/AI ghi dự kiến nếu chưa làm; không cần đổi C++ thành sketch.ino | Chưa sửa B |
| A30 | B Wokwi hoàn toàn open source, GPU Colab miễn phí, AI không chạy được trên ESP32 | Thu hẹp khẳng định theo nguồn/phiên bản | Không gọi toàn bộ Wokwi open source; GPU phụ thuộc khả dụng; khả năng AI tùy model/board; PC là lựa chọn kiến trúc hiện tại | Chưa sửa B |
| A31 | B optocoupler luôn cách ly hoàn toàn; mô phỏng dễ bị hiểu là mạch thật | Theo schematic/module và cách đấu thực tế | Ghi sim-only; hardware cần nguồn, chuyển mức, warmup/hiệu chuẩn; không tự kết luận có cách ly chỉ vì có optocoupler | Chưa đồng bộ B; hardware ngoài phạm vi hiện tại |
| A32 | B đặt web/mobile như mục tiêu chính, T tùy chọn | Đề xuất để dashboard P2 nếu chưa cam kết riêng với thầy | Ghi tùy chọn/hướng phát triển; không trì hoãn local+MQTT+AI bắt buộc để làm UI | Chưa triển khai |
| A33 | B Ch4–6/phụ lục phần lớn mẫu; links/version/figures thiếu | Dùng sản phẩm và bằng chứng thực | Điền flow, module, ảnh, kết quả, giới hạn; nguồn/đóng góp/AI hỗ trợ/biên bản và links theo thực tế | Chờ S8/S9 |
| A34 | B có tham khảo trùng[2]/[3], mục mẫu, số liệu PCCC thiếu nguồn cụ thể | Sửa nguồn, không mặc định số liệu sai | Tìm nguồn gốc số liệu hoặc bỏ/viết lại; đủ nguồn thực và dataset, cập nhật mục lục/caption khi hoàn tất | Chưa sửa B |
| A35 | B tự đặt18/20; T cần13TC×20 và phân tích fail; C host tests | Theo phép thử thực và các điều kiện bắt buộc | Không dùng tỉ lệ tổng để che lỗi nguy hiểm; lưu từng lượt, ≥1ảnh/TC, nêu fail và sửa; host tests không thay260lượt | Chờ S8 |

## Kế hoạch implement và điều kiện hoàn thành

Đây là thứ tự triển khai đề xuất. Các ô chưa đánh không phải cam kết đã thực hiện. Bảng chân/servo policy/model chưa chốt cần được giải thích thành lựa chọn cụ thể trước khi code phụ thuộc.

| Bước | Mục tiêu | Tệp hoặc sản phẩm bị ảnh hưởng | Điều kiện chuyển bước | Trạng thái |
|---|---|---|---|---|
| S0 | Ôn căn bản và theo một tín hiệu xuyên hệ thống | Giải thích trên mạch, main/sensors/safety/outputs/telemetry | Người dùng tự mô tả đầu vào→luật→FSM→tải→log; không cần thuộc C++ | Chưa hoàn tất vòng học |
| S1 | Chốt thiết kế local có LDR/servo | KB D01–D08, bảng GPIO, bảng đầu ra theo state | Có pinout không xung đột, quy tắc LDR và servo boot/mở/đóng/lỗi/ACK | Chốt hành vi và chọn thông số R5; ngưỡng/góc còn xác nhận ở S5 |
| S2 | Sửa mất DHT sau nguy hiểm | safety.h/.cpp, sensors nếu cần, test_safety, log reason, test guide | Regression60C→lỗi pass; timeout/ACK/nhánh MQ-LDR không bị phá; build/host test pass | Đã sửa, build/host tests pass R5 |
| S3 | Thêm LDR demo thay nút lửa chính | diagram, config, sensors/SensorSnapshot, telemetry/display, wiring tests | Thay sáng→giá trị→cờ lửa→FSM; có ngưỡng/hysteresis và test ảnh/log | Code/diagram/log/core tests xong R5; đã có ADC LDR và xác nhận còi từ người dùng; S5 chưa đủ |
| S4 | Thêm servo cửa, giữ hai relay | diagram, config, output state/driver, thư viện/pwm, UI/log, tests | Các state đúng policy cửa; servo+còi không xung đột; relay giữ chức năng | Code/diagram/pulse và FSM tests xong R5; người dùng xác nhận đóng cửa, đã thấy hai LED tải; còn chuỗi đầy đủ S5 |
| S5 | Chốt nhánh local trên Wokwi | Firmware cuối local, hướng dẫn, ảnh/log/version | Checklist local đủ để đóng; AI TC nghiệm thu riêng | HOÃN theo người dùng28/10, chưa đủ L01–L10; không chặn triển khai S6 |
| S6 | MQTT + hợp đồng + mock test | Network/contract/payload modules, queue/task, config mẫu, mock Python, tests | Parser/fusion/queue, hai chiều/reconnect và đo runtime local khi mạng lỗi | R6 code/build/host tests/PC broker smoke pass; chưa chạy runtime Wokwi |
| S7 | Adapter/publisher + model AI | Adapter/replay/plugin và manifest; model/weights/metrics sau | Plugin/replay theo contract; model thật cần kiểm định riêng | R7 có khung, replay test pass; model/train/metrics HOÃN theo người dùng |
| S8 | Kiểm thử và bằng chứng | Regression/capture/tracker + bảng13×20 | Tooling chạy được; nghiệm thu chỉ đóng khi đủ lượt thực/model/ảnh | R7 tooling/testhost xong; formal260NOT_RUN, không đánh hoàn tất nghiệm thu |
| S9 | Đồng bộ và đóng gói báo cáo | DOCX, hình, tham khảo, phụ lục, repo/ZIP/Wokwi link | Nội dung đúng sản phẩm đã test, link mở được, nguồn/đóng góp/khai báo thật | Chưa làm |

Sửa mô tả thiết kế trong báo cáo có thể tiến hành sau S1; không phải đợi S9 mới sửa mọi chương. Kết quả ở Chương5 chỉ điền sau phép thử tương ứng. Có thể khảo sát tài sản AI trong lúc test local, nhưng người dùng đã yêu cầu để phần AI làm sau, không tự triển khai trong lượt cập nhật KB này.

<a id="s0"></a>

### S0 Checklist học lại qua đồ án

Vòng giải thích S0 ngày27/10/2026 đi qua linh kiện/GPIO/ADC/PWM, setup-loop và lịch millis, SensorSnapshot→luật→FSM→outputs→LCD/log, ví dụ MQ/lửa/DHT/ACK/timeout, vai trò file và vị trí AI/MQTT tương lai. Đây là nội dung ôn tập; H01–H06 vẫn chưa đánh hoàn thành cho tới khi người dùng thực hành hoặc tự diễn giải được. Chưa sửa firmware trong lượt ôn tập.

- [ ] H01: Chỉ đúng vai trò ESP32, MQ, LDR/nút giả hiện tại, DHT, ACK, relay, servo dự kiến, LCD và log.
- [ ] H02: Phân biệt GPIO với vị trí chân; HIGH/LOW, analog/digital, ADC, PWM và pull-up; giải thích ACK active LOW.
- [ ] H03: Phân biệt số đo ADC, ngưỡng, mức nguy hiểm0/1/2 và state; không gọi ADC là ppm.
- [ ] H04: Theo flow setup/loop→sensors→SensorSnapshot→SafetyController→outputs→LCD/log trên code hiện tại; nói rõ đoạn nào chưa có.
- [ ] H05: Tự dự đoán kết quả khi MQ qua ngưỡng hoặc nhấn lửa; hiểu vì sao hết nguy hiểm chưa tự về NORMAL và ACK không phải nút tắt nguy hiểm.
- [ ] H06: Hiểu sample period khác reaction latency; biết AI và MQTT nằm ngoài code local hiện tại.

<a id="s1"></a>

### S1 Checklist chốt thiết kế còn thiếu

- [x] P01: Người dùng chốt giữ V1 ngày27/10/2026. Việc sửa board/hình trong DOCX vẫn chưa làm, theo A01/R01.
- [x] P02: Người dùng chốt LDR analog, ánh sáng tăng đủ mạnh là lửa giả lập ngày27/10/2026. Lịch/ngưỡng/hysteresis/chân và khảo sát ADC chưa làm, theo P07/I03/I04.
- [x] P03: R5 chọn GPIO33, LEDC50Hz16bit kênh8/group1, không thêm thư viện; source core2.0.17 xác nhận timer khác group còi0/group0. Wiring/build pass; chuyển động servo+còi chờ S5.
- [x] P04: Người dùng chốt policy cửa ngày27/10/2026: boot chưa có nguy hiểm/NORMAL/WARNING đóng; FIRE mở; RECOVERY/timeout giữ mở; chỉ đóng sau ACK an toàn hợp lệ. Góc0/90 là ứng viên để kiểm tra, chưa coi là kết quả đã chạy.
- [x] P05: Người dùng chốt D08 ngày27/10/2026: giữ nguyên nhân nguy hiểm nhiệt khi DHT mất dữ liệu đến mẫu hợp lệ chứng minh hết điều kiện; vẫn dừng bơm khi timeout60s. Timeout không phải bằng chứng nhiệt đã giảm; fault không ghi DANGER_CLEARED.
- [x] P06: Đã ghi bảng đầu ra thiết kế đích dưới D04/D05 ngày27/10/2026. Đây là yêu cầu được chốt, chưa là code hoặc bằng chứng runtime.
- [ ] P07: R5 đã chọn LDR32/100ms/ngưỡng500-750 ADC, servo33/0-90°/50Hz kênh8; **chưa khảo sát runtime** quan hệ ánh sáng–ADC và góc thực. Ghi ảnh/log trước khi đóng mục này.

<a id="s2-s4"></a>

### S2–S4 Checklist implementation local

- [x] I01: Viết regression cho DHT nguy hiểm→read fail/stale; kiểm tra mẫu phục hồi thấp/cao, rate sau lỗi và nhiều nguồn đồng thời. — Đã thực hiện R5; bằng chứng build/host/hash ở cuối KB, quan sát runtime riêng ở S5.
- [x] I02: Sửa A16, lưu expected/observed và bảo toàn hạn60s/khóa/ACK; không dùng bơm vô hạn để chữa lỗi giữ chốt. — Đã thực hiện R5; bằng chứng build/host/hash ở cuối KB, quan sát runtime riêng ở S5.
- [x] I03: Sửa diagram/config/sensors cho LDR; cập nhật valid/age nếu dùng; bỏ vai trò nút đỏ làm nguồn chính hoặc ghi rõ test phụ. — Đã thực hiện R5; bằng chứng build/host/hash ở cuối KB, quan sát runtime riêng ở S5.
- [x] I04: Cập nhật log/LCD có giá trị LDR và ý nghĩa giả lập; test dao động biên và nguồn sáng thay đổi. — Đã thực hiện R5; bằng chứng build/host/hash ở cuối KB, quan sát runtime riêng ở S5.
- [x] I05: Thêm servo driver và trạng thái cửa theo P04; giữ hai relay; không để servo làm xung đột tần số còi. — Đã thực hiện R5; bằng chứng build/host/hash ở cuối KB, quan sát runtime riêng ở S5.
- [x] I06: Cập nhật wiring fixture/checks, core tests và hướng dẫn runtime; không sửa fixture chỉ để test pass nếu chưa đối chiếu linh kiện. — Đã thực hiện R5; bằng chứng build/host/hash ở cuối KB, quan sát runtime riêng ở S5.
- [x] I07: Build ESP32 bản mới và chạy host/static tests phù hợp; lưu version/hash của source và diagram; chỉ retest thêm khi có thay đổi/fail/concern. — Đã thực hiện R5; bằng chứng build/host/hash ở cuối KB, quan sát runtime riêng ở S5.

<a id="s5"></a>

### S5 Checklist runtime local bản có LDR và servo

**HOÃN theo yêu cầu người dùng28/10/2026; các ô mở không chặn triển khai S6. Chưa được tính hoàn tất.**

Đã có bằng chứng từng phần: [LDR và còi](evidence/local-r5-user-ldr-2026-10-28.txt), [LED tải sáng/RECOVERY](evidence/local-r5-user-servo-pending-2026-10-28.txt), [NORMAL trong log](evidence/local-r5-user-normal-2026-10-28.txt), [người dùng xác nhận đóng cửa](evidence/local-r5-user-door-closed-2026-10-28.txt). Các ô dưới vẫn mở vì mỗi ô bao gồm cả chuỗi/điều kiện chưa thử đầy đủ; không có nghĩa mọi chức năng đều chưa chạy.

- [ ] L01: Boot đúng firmware/diagram/version; MQ thấp, DHT28/45, LDR nền; đầu ra đúng state boot đã chốt.
- [ ] L02: MQ thấp→warning→danger→thấp: ADC đổi tương ứng, hysteresis đúng; LED tải COM-NO chứng minh hai relay.
- [ ] L03: LDR nền→sự kiện giả lửa→nền: giá trị đọc/cờ/nguồn/state/servo/tải khớp; đo phản hồi, không gọi đây là sensitivity lửa thật.
- [ ] L04: DHT thay T/H đọc được theo3s; nhiệt tuyệt đối và rate kích riêng đúng dt, không nhầm mẫu đầu/sau lỗi với rate đã đo0.
- [ ] L05: Chuỗi nhiệt nguy hiểm→DHT lỗi: hành vi đúng P05, log không giả định nhiệt đã giảm; lửa/MQ còn có quyền kích.
- [ ] L06: NORMAL/WARNING/FIRE/RECOVERY: LCD/đỏ/xanh/còi/servo/hai tải đúng bảng; servo và còi chạy đồng thời ổn.
- [ ] L07: ACK khi nguy hiểm không reset; bounce/giữ từ boot/nhấn sớm không được tính về sau; an toàn3s rồi nhấn mới thì reset đúng.
- [ ] L08: Giữ nguy hiểm60s→timeout; tiếp tục giữ thêm10s không tái bật bơm; cửa theo policy; an toàn+ACK rồi nguy hiểm mới kích lại.
- [ ] L09: Log chữ dễ hiểu; CSV đúng cột/nguồn/event và tuổi mẫu; thu số đo latency trong lúc đọc DHT/in log, nêu giới hạn.
- [ ] L10: Lưu ảnh/log input/output của từng trường hợp, mã phiên bản và fail; cập nhật KB, không tuyên bố pass nếu chỉ thấy log lệnh relay.

<a id="s6"></a>

### S6 Checklist MQTT và hợp nhất dùng mock

Bổ sung bằng chứng người dùng: [summary log ESP→broker→PC](evidence/s6-user-mqtt-summary-2026-10-28.json),24snapshot ở15,864–38,864s; UTC0, MQ3628/localdanger, ai_accepted0. Đã chứng minh outbound telemetry, chưa chứng minh nhậnAI hoặc lỗiNTP kéo dài. R7 khởi động NTP sauWi-Fi với3server; cần xác nhận runtime, không bỏ validationUTC.

**R6 đang triển khai/kiểm chứng.** [Contract, file flow, cấu hình và test](reference/s6-mqtt-contract.md). Chọn ESP-MQTT có sẵn trong SDK Arduino core2.0.17, thay đề xuất PubSubClient để lấy được metadata retained và quản lý socket bằng task. ArduinoJson6.21.5; Paho2.1.0. Broker demo HiveMQ/prefix riêng; chưa chứng minh ESP32 tới broker trong Wokwi. [Build](evidence/s6-build-2026-10-28.log), [host](evidence/s6-host-2026-10-28.log), [PC↔localhost broker](evidence/s6-broker-smoke-2026-10-28.log). Checkboxes đóng ở mức contract/core được ghi rõ; các ca mạng/latency trên MCU vẫn mở.

- [x] N01: Chốt thư viện/version/broker demo/topic/schema dùng chung firmware/mock, cấu hình mẫu không secrets. — R6 chọn ESP-MQTT SDK, JSON6.21.5, Paho2.1.0, schema v1/TTL15s/confidence0.8; không có broker dự phòng đã test. ESP32↔broker thực còn chờ runtime.
- [ ] N02: Local khởi động và tiếp tục hoạt động khi không Wi-Fi hoặc broker không phản hồi; reconnect có backoff và không chặn vòng local.
- [ ] N03: MQTT hai chiều; subscribe lại sau mọi reconnect; test mất mạng từ boot và trong khi đang FIRE.
- [x] N04: Parser reject sai cú pháp/thiếu/trùng/trường lạ/type/nhãn/confidence/size; gói lỗi không gia hạn freshness. — Host test chạy codeparser thật dướiASan/UBSanPASS; callbackdrop/flood trên MCU chờ runtime.
- [ ] N05: Chốt TTL, thời gian gửi/nhận, sai lệch đồng hồ, bản tin cũ/tương lai/duplicate/retained và session restart; hiển thị AI mất/không khả dụng.
- [x] N06: Core max(local,AI hợp lệ), AI normal/expired không hạ local, không bypassFSM/timeout/ACK. — Host fusion/TTL/source/timeout/ACKPASS; chưa phải MCU integrationPASS.
- [ ] N07: Phân biệt source LOCAL/AI/cùng nguồn và các event; chọn QoS theo chiều thực tế; kiểm tra parser/buffer/flood giới hạn.
- [ ] N08: Đo lại latency local khi mạng lỗi; ghi rõ mock dùng test protocol, chưa tính là AI đã làm.

<a id="s7"></a>

### S7 Checklist adapter và AI thay sau

Theo yêu cầu mới28/10: đã làm đường tích hợp để thay model sau; chưa train/tảiweights. [Hướng dẫn và giới hạn](s7-s8-guide.md). M01–M07 dưới đây chưa hoàn tất. Cập nhật: người dùng đã nạp model pretrained và thử ảnh/webcam; có [observer/plugin YOLO](ai-observation.md) nhưng chưa nghiệm thu MQTT với model thật. M08–M10 là khung đã thực hiện.

- [x] M08: `ai_adapter.py` validation/contract; `ai_publish.py` replay hoặc plugin, confidence hữu hạn, timestamp capture; unknown/camera lỗi không tự phát bìnhthường. Unit test và replay qua localhostbrokerPASS; camera thật chưa chạy.
- [x] M09: Giao diện `module:function` cho model riêng, nhận frameBGR; detector helperFire ưu tiênSmoke, khôngbox→unknown. Chưa khóa classifier/detector hoặc thêm temporalfilter chưa kiểm định.
- [x] M10: Mẫu modelmanifest cóweights/hash/license/preprocessing/dataset/metrics đểnull với trạng tháiDEFERRED; logREPLAY_MOCK/PLUGIN_UNVERIFIED không tự biến thànhmodel thật.

- [ ] M01: Kiểm kê dataset/notebook/weights/inference của thành viên phụ trách; chốt classifier hoặc detector và ghi quyết định thay D07.
- [ ] M02: Manifest nguồn/license/số lượng/chia tập theo video hoặc nguồn; có ảnh nền và ảnh dễ nhầm, không để frame cùng video rò train/test.
- [ ] M03: Nếu classifier: định nghĩa3nhãn; nếu detector: Fire/Smoke boxes + ảnh âm tính + adapter, quy tắc ảnh có cả2loại và camera unavailable.
- [ ] M04: Train/fine-tune thật; lưu config/seed/version/weights và tập test độc lập; mục tiêu mAP85% hoặc tiêu chí khác không được ghi như kết quả.
- [ ] M05: Đo metrics theo task, recall lửa và báo giả; định nghĩa phép đo cấp hệ thống riêng; FPS/latency ghi máy/độ phân giải thực.
- [ ] M06: Webcam/video→model→adapter→MQTT→ESP hoạt động; không có detection không đồng nghĩa cảnh chắc chắn an toàn; camera lỗi tách riêng.
- [ ] M07: Chốt policy ảnh nến/bật lửa/ánh đỏ/hơi nước/che khuất, temporal filtering nếu chọn; nêu đánh đổi báo giả/bỏ sót bằng kết quả.

<a id="s8"></a>

### S8 Checklist công cụ và nghiệm thu 13 tình huống

**Đã hoàn thiện công cụ, chưa hoàn tất nghiệm thu.** [Report phần mềm R7](evidence/s7s8-final-checks-2026-10-28/report.json): build/host/unit/PC-broker smokePASS, hostscenario240PASS/20DEFERRED. Mọi lượt formal ở bảng gốc vẫnNOT_RUN; không chuyển kết quảHOST_SYNTHETIC sang kết quảWokwi.

- [x] E05: Bộ13TC×20hàng regression core với virtualmillis;12TC×20PASS, TC11×20DEFERRED vì chưa cóảnh/model. ASan/UBSan; CSV ghi rõdomain/modelMOCK_ONLY.
- [x] E06: `capture_mqtt.py` lưu JSONL exclusive với UTC/monotonic/topic/QoS/identity; `capture-summary` kiểm tra một số mâu thuẫn dữ liệu và phiên bản. PCfixture qua broker đã test; chưa chứng minh tải thực.
- [x] E07: `s8_track.py` dùng duy nhất bảng260lượt gốc; record atomic/filelock/audit, từ chối host/mock domain hoặc modelmock cho model-dependentPASS. Unit tests dùng bảng tạm; bảng gốc không đổi.
- [x] E08: `verify_project.py` một lệnh build/core/Python/scenarios/broker tùy chọn, log/hash/report; lỗi hoặc chạy chưa đủ stage không được báoPASS. Không chạy model/Wokwi hoặc tự ghiPASSnghiệmthu.

Mỗi TC dưới đây cần20lượt thật, expected/observed, firmware/model version, thời gian, ảnh/log; không đánh `[x]` chỉ vì một lần thử hoặc unit test. Bảng lượt hiện có `../../tests/integration-results.csv` nằm ngoài repo firmware; giữ bảng này hoặc chuyển có kiểm soát khi đóng gói, không tự tạo bộ kết quả song song mâu thuẫn. Các TC bổ sung không thay thế13TC gốc.

| TC | Phép thử gốc | Phụ thuộc | Kết quả đang có |
|---|---|---|---|
| TC01 | Bình thường | Local + AI để nghiệm thu toàn hệ | NOT_RUN |
| TC02 | MQ cảnh báo | Local | NOT_RUN |
| TC03 | MQ nguy hiểm, bơm và van | Local | NOT_RUN |
| TC04 | Lửa cục bộ | Local LDR thay DO phải mô tả cách tạo tín hiệu tương đương | NOT_RUN |
| TC05 | Tốc độ tăng nhiệt | Local DHT | NOT_RUN |
| TC06 | AI lửa khi cảm biến nền | AI thật + MQTT | NOT_RUN |
| TC07 | Biên ngưỡng khói | Local | NOT_RUN |
| TC08 | Mất nguồn AI | AI/MQTT/TTL | NOT_RUN |
| TC09 | Bản tin sai định dạng | MQTT/parser | NOT_RUN |
| TC10 | AI normal, local danger | Hợp nhất + AI/MQTT | NOT_RUN |
| TC11 | Ảnh dễ nhầm | AI thật | NOT_RUN |
| TC12 | Chữa cháy quá thời gian | Local + hợp nhất bản cuối | NOT_RUN |
| TC13 | ACK, giữ latch | Local + bản tích hợp cuối | NOT_RUN |

- [ ] E01: Hoàn thành20lượt của từng TC, đủ260lượt; ghi fail thật thay vì tự đặt số pass.
- [ ] E02: Có≥1ảnh minh chứng/TC và log phù hợp; minh chứng cả hai nhánh cùng chạy và nguồn kích hoạt.
- [ ] E03: Thêm regression DHT nhiệt cao→lỗi, LDR biên, cửa ở từng state/timeout/ACK, boot không mạng, reconnect chậm và nhiều nguồn đồng thời.
- [ ] E04: Xử lý mọi fail theo mức độ; không lấy18/20 hoặc tỉ lệ tổng để kết luận lỗi chức năng bắt buộc đã đạt. Sửa source/model thì chạy lại các tình huống bị ảnh hưởng.

<a id="s9"></a>

### S9 Checklist báo cáo và gói nộp

- [ ] R01: Sửa A01–A08/A17–A19 trong Ch1–3: board, MQ, LDR, hai relay+servo, lịch, timing, loại còi và định dạng log.
- [ ] R02: Chốt bảng GPIO, sơ đồ thật, block diagram, FSM và bảng đầu ra theo state; mô tả khác biệt có lý do so với khung T.
- [ ] R03: Ch4 mô tả module/file/flow/build/version/network/model thật; xóa các chỉ dẫn mẫu sau khi đã điền nội dung.
- [ ] R04: Ch5/Phụ lục D lấy kết quả từ E01–E04; tách host/unit/protocol mock/integration/metrics AI; có phiên bản tương ứng.
- [ ] R05: Ch6 nêu giới hạn sim, LDR thay tín hiệu, AI chạy PC, mất mạng/camera, dữ liệu nhỏ và tính học thuật; không mô tả tính năng chưa làm như đã có.
- [ ] R06: Sửa nguồn/mục tham khảo trùng, số liệu PCCC chưa có nguồn cụ thể, phát biểu tuyệt đối về Wokwi/GPU/AI/optocoupler/gas; dùng nguồn thật, đủ thông tin và dataset license.
- [ ] R07: Điền phân công/đóng góp/nhóm trưởng/biên bản và khai báo AI hỗ trợ theo xác nhận thực, không tự suy đoán đóng góp.
- [ ] R08: Cập nhật mục lục/caption/danh mục hình bảng, render kiểm tra DOCX; các công thức T=1s/mAP85% có trong Word, không nhầm trích text mất công thức là nội dung trống.
- [ ] R09: Link repo/Wokwi public mở được ở chế độ chưa đăng nhập; firmware build được theo hướng dẫn; gói ZIP đúng yêu cầu có đủ tài liệu/model/minh chứng, không secrets/.pio.

### P2 Checklist mở rộng nếu chọn làm

- [x] X01: Người dùng đã chọn triển khai dashboard; có Streamlit/MQTT/SQLite chỉ đọc, biểu đồ/history/AI/stale và test phần mềm. Nghiệm thu Wokwi dashboard theo guide; không có remotecontrol. Mobile riêng chưa thuộc phạm vi đã làm.
- [ ] X02: Nếu lên phần cứng thật, lập thiết kế riêng nguồn/chuyển mức/tải/cách ly/servo/warmup/hiệu chuẩn. Không đánh hoàn thành hardware từ kết quả simulator.

## Những gì đã có bằng chứng và giới hạn của bằng chứng

- [x] V01: Review ba bên; [bản so sánh](../../docs/review-2026-10-27/three-way-review.md). DOCX gốc không sửa trong review.
- [x] V02: Phase1 R4 có log DHT39lần/0lỗi và thay T/H/nút, theo [log người dùng](../../docs/evidence/phase1-user-runtime.txt). Đây là bản cũ trước LDR/servo, chưa chứng minh Phase2 runtime đầy đủ.
- [x] V03: Build Phase2 trước các thay đổi mới có [build log](evidence/build.log); phải build lại sau sửa source/diagram.
- [x] V04: Wiring và8nhóm host test Phase2 đã pass, gồm20.000bước tổng hợp; [host log](evidence/phase2-host-test.log). Chưa bao phủ A16, không thay260lượt tích hợp.
- [x] V05: A16 đã tái hiện fail trước sửa; R5 bổ sung regression vào core tests và pass sau sửa. Review cũ giữ nguyên như chứng cứ lịch sử; [host test R5](evidence/local-r5-host-test.log) ghi kết quả hiện tại.
- [x] V06: Người dùng chọn LDR, đồng ý hai relay+servo, DHT3s, để AI làm sau; đã ghi D03–D07.
- [ ] V07: Hoàn tất local bản LDR/servo và A16 đã sửa; đóng khi S1–S5 có đủ bằng chứng.
- [ ] V08: Hoàn tất đề tài tích hợp; đóng khi S6–S9 đạt phạm vi đã thống nhất và có dữ liệu thực.

## Nhật ký thay đổi KB

| Ngày | Thay đổi | Lý do | Ảnh hưởng và trạng thái |
|---|---|---|---|
| 27/10/2026 | Tạo D01–D07, chọn LDR và hai relay+servo, DHT3s; AI để sau | Người dùng đồng ý hướng align sau so sánh ba bên | Chưa sửa firmware/diagram/DOCX |
| 27/10/2026 | Gom A01–A35, S0–S9 và checklist H/P/I/L/N/M/E/R/X/V vào cùng KB | Người dùng yêu cầu một nơi track cả chênh lệch, đề xuất và triển khai | KB là nơi cập nhật tiến độ chính; review và hướng dẫn cũ giữ làm tham chiếu |
| 27/10/2026 | Người dùng chốt4nhóm S1: V1, LDR analog tăng sáng, policy cửa, xử lý DHT lỗi sau nguy hiểm | Phản hồi đồng ý trực tiếp của người dùng | Cập nhật D01/D03/D05/D08 và P01/P02/P04/P05/P06; pinout/ngưỡng/PWM, code và test vẫn chờ |
| 27/10/2026 | Implement LOCAL R5: DHT hold, LDR32/100ms, servo33/50Hz khác group còi, log37cột | Người dùng yêu cầu bắt đầu S2–S5 | Build/10nhóm core tests và wiring pass; S5 chưa chạy được do CUA timeout; DOCX/AI/MQTT chưa sửa |

## Cách duy trì KB

Mỗi thay đổi tiếp theo ghi ngày, quyết định, lý do, phương án bị thay, file/kiểm thử bị ảnh hưởng và trạng thái triển khai. Nếu sửa quyết định cũ, giữ lịch sử và ghi quyết định thay thế; không biến kế hoạch thành thông báo đã hoàn thành.

Khi đóng một ô, thêm ngày, phiên bản và link bằng chứng ngay sau ô hoặc trong hàng liên quan. Khi phát hiện lỗi mới, tạo A/issue và checklist regression liên quan. Giữ cùng trạng thái giữa bảng tổng quan và các ô chi tiết; không đánh một bước hoàn thành nếu điều kiện chuyển bước chưa đạt. Người phụ trách và deadline chưa được nhóm phân công thì để chưa phân công, không tự gán.

Đối chiếu gốc: báo cáo AutoRecovered và hướng dẫn Phần F tại thư mục môn học. Bản review trước quyết định LDR/servo nằm ở `../../docs/review-2026-10-27/three-way-review.md` và được giữ như ảnh chụp hiện trạng trước thay đổi, không phải tài liệu thiết kế mới nhất.

## Bằng chứng LOCAL R5 và bàn giao S5

- [Build ESP32 R5](evidence/local-r5-build.log): SUCCESS; firmware.bin/elf đã tạo.
- [Wiring và host tests R5](evidence/local-r5-host-test.log): 10nhóm core +20.000bước tổng hợp, ASan/UBSan; gồm regression DHT và policy cửa/LDR/pulse. Không tính thành lượt integration.
- [Hash source/diagram/binary](evidence/local-r5-sha256.json): nhận diện phiên bản để thu bằng chứng tiếp.
- [Giới hạn agent runtime](evidence/local-r5-runtime-status.txt): truy cập VS Code qua Computer Use timeout. Sau đó người dùng cung cấp [log boot R5](evidence/local-r5-user-boot.txt): đã chứng minh MCU chạy R5 và lệnh FIRE do MQ cao; chưa có ảnh tải/servo hoặc đủ các tình huống S5.
- [Hướng dẫn test R5](archive/phase2-testing-r5.md): khởi động đúng bản, input nền, LDR/relay/servo/ACK/timeout và giới hạn thử lỗi DHT.

Thông số LDR500/750 là lựa chọn demo ban đầu theo mạch chia áp (sáng tăng→ADC giảm), chưa được hiệu chuẩn bằng runtime. Không tự gọi100lux/20000lux luôn cho một ADC cố định. LDR nguồn3V3, MQ vẫn5V mô phỏng; không gọi đây là bản hardware đã an toàn/hiệu chuẩn. Analog hở dây có thể vẫn trong dải nên cờ hợp lệ/stale không bảo đảm phát hiện mọi lỗi dây.

### S5 nhận log người dùng lần đầu ngày27/10/2026

Nguồn: [trích log và bảng snapshot](evidence/local-r5-user-boot.txt). Đã thấy boot đúng R5, NORMAL→FIRE tại1,70s vì MQ3628ADC; LDR2045 không báo lửa; DHT lần1 đọc28°C/45%,0lỗi tại log3,70s. Hai relay lệnh ON, cửa lệnh90°, còi/đỏ ON đúng state FIRE. Đây là kết quả một đoạn boot, **không phải toàn bộ S5 pass** và chưa có lượt cuối nào trong260integration được đánh PASS.

L01 chưa đóng vì chưa đưa về NORMAL và chưa có ảnh tải/cửa. L02/L03/L06/L08 còn chờ thao tác thay đầu vào, quan sát servo/relay, ACK và đủ60s. DHT WAIT trước lần đọc đầu, rate chưa đủ2mẫu là trạng thái bình thường. Thao tác kế: MQ<1700, LDR>=750, DHT28/45; đợi RECOVERY và an toàn3s rồi nhấn ACK mới.

### S5 nhận RECOVERY sẵn sàng ACK ngày28/10/2026

[Trích dữ liệu người dùng](evidence/local-r5-user-recovery-2026-10-28.txt) tại506,83s/507,83s: local0/NONE, MQ1675, LDR2683 không lửa giả, DHT28/45/rate0; bộ đếm168lần đọc/0lỗi. Lệnh bơm/van/còi OFF, đỏ ON, cửa OPEN90°, timeout lock=true và ackReady=true. Trạng thái chờ xác nhận đúng; FLAME là nguồn chốt lịch sử, không phải nguy hiểm hiện tại.

Chưa đóng L07/L08/L10 hoặc TC13: chưa có event ACK_SAFE, ảnh cửa đóng/tải, hay timestamp trước/sau mốc60s. Thao tác tiếp: giữ đầu vào nền, thả rồi nhấn ACK mới khoảng0,2s và thu event/state/quan sát cửa.

### S5 nhận NORMAL sau thao tác ACK ngày28/10/2026

[Snapshot522,84s và523,84s](evidence/local-r5-user-normal-2026-10-28.txt) đã NORMAL/local0, nguồn chốtNONE/NONE, bơm/van/còi/đỏ OFF và cửa lệnhDONG0°. MQ1675/LDR2683 nền; DHT173→174lần đọc/0lỗi, T28/45/rate0. So với RECOVERY trước đó, đã thấy trở về NORMAL và xóa nguồn chốt sau hướng dẫn ACK. Không có event ACK_SAFE trong đoạn gửi nên chưa đo timestamp/debounce/lock; chưa xác nhận servo đóng thực bằng mắt. Không đánh đạt toàn bộ L07/TC13 hoặc20lượt.

Bước kế: giữ MQ/DHT nền, tăng sáng LDR đếnADC≤500 để test riêng nguồn lửa giả, quan sát haiLED tải và servo, thu event/snapshot; sau đó hạ sáng về nền để test RECOVERY giữ cửa mở.

### S5 LDR vượt ngưỡng và có tiếng còi ngày28/10/2026

[Phản hồi người dùng](evidence/local-r5-user-ldr-2026-10-28.txt): ở263lux ADC1378 chưa kích; tăng lux tiếp làm ADC<500 và còi kêu. Đã có bằng chứng người dùng về chiều ánh sáng→ADC và còi khi vượt ngưỡng. Chưa có giá trị lux cao cụ thể, event/state/reason, haiLED tải hoặc servo thực. L03/L06/P07 vẫn chưa đóng đầy đủ; chưa tự khẳng định FIRE chỉ từ tiếng còi vì WARNING cũng có còi.

Kế tiếp: đối chiếu FIRE_SUPPRESSION/FLAME trong log, haiLED BOM/VAN sáng và servo mở; sau đó giảm sáng về40lux (ADC≥750), kiểm tra RECOVERY giữ cửa mở và ACK an toàn3s đưa NORMAL/cửa đóng.

### S5 hai LED tải sáng, servo chưa quan sát chuyển động ngày28/10/2026

[Phản hồi người dùng và kiểm tra dây/driver](evidence/local-r5-user-servo-pending-2026-10-28.txt): haiLED vàng BOM/VAN đã sáng sau kích LDR; người dùng chưa thấy servo di chuyển. Ghi nhận đầu ra relay có phản ứng bằng quan sát, **không đánh đạt servo hoặc L06/S4 runtime**. Chưa có dòng lệnh cửa hiện tại của lượt này. Dây PWM33/VIN/GND và phép đổi duty đúng theo cấu hình source, nhưng chưa chứng minh dạng xung Wokwi.

Theo dõi A36 — servo không thấy di chuyển: cần đối chiếu NORMAL/DONG0→FIRE/MO90 và quan sát tay servo trong cùng lượt; nếu lệnh thay đổi mà tay đứng yên, kiểm tra PWM runtime. Chưa kết luận nguyên nhân, chưa thay kênh PWM/thư viện hay tuyên bố sửa. Async đã hỏi người dùng dòng cửa trước/sau hoặc ảnh servo.

S5 bổ sung A36: log3522,81–3524,81s vẫn RECOVERY, cửa lệnhMO90°, ackReady=true, timeoutlock=false; MQ/LDR/nhiệt nền và DHT1171lần/0lỗi. Giữ cửa mở khi hạ sáng là policy đúng, chưa chứng minh servo bị đứng hoặc đã chạy. Chưa có cặp lệnh0→90/90→0 kèm quan sát. Cần ACK mới→NORMAL/DONG0 và xem tay servo; chưa sửa PWM.

### Cập nhật log gọn ngày28/10/2026

Theo yêu cầu người dùng: tăng kLogIntervalMs1000→3000ms, gom2–3thông số liên quan mỗi dòng; giữ cửa lệnh/ACK, nguyên nhân hiện tại/chốt, mask, dữ liệu và tuổi mẫu, DHT lỗi/rate, đầu ra, timeout và giữ nguy hiểm nhiệt. EVENT chuyển state vẫn in ngay; không đổi lịch cảm biến, FSM, PWM hoặc ngưỡng. CSV giữ37cột nhưng snapshot theo lịch3s; bộ nghiệm thu đo latency nên dùng EVENT/timestamp đầu vào, không suy từ snapshot định kỳ. Servo A36 vẫn chưa xác nhận chuyển động; cập nhật log không được tính là sửa servo.

### A37 Còi được lệnh bật nhưng người dùng không nghe ngày28/10/2026

Log người dùng tại25,70s: FIRE level2,mask7 (khói warning/danger+lửa giả),MQ3543,LDR448,DHT28/45/8lần đọc0lỗi; lệnh tải/còi ON,cửa90°. Đây là lệnh, chưa chứng minh sóng GPIO/âm thanh. Đối chiếu hash xác nhận bản LOG3S không đổi driver outputs/safety/diagram so vớiR5. Buzzer đang volume0.1.

Thay đổi chẩn đoán: volume0.1→0.5 trong diagram; thêm outputDiagnostics đọc ledcReadFreq(0/8) và ledcRead(8), log ngắn mỗi3s. Không đổi tần số/kênh/logic còi hoặc servo; CSV vẫn37cột. Readback là cấu hình thanh ghi LEDC, không phải feedback vị trí servo hoặc microphone/GPIO waveform. Mong đợi khi FIRE: coi2000Hz,cua50Hz,duty4915/65536; khiNORMAL: coi0Hz,cua50Hz,duty1638/65536. Nếu readback đúng mà không nghe, cần kiểm tra audio VSCode/hệ điều hành và dạng sóng thực trước khi kết luận. A36 servo vẫn chưa xác nhận chuyển động; A37 chưa được coi đã sửa chỉ vì tăng âm lượng/build.

### S5 người dùng xác nhận đóng cửa ngày28/10/2026

[Phản hồi trực tiếp](evidence/local-r5-user-door-closed-2026-10-28.txt): người dùng đã đóng được cửa và yêu cầu commit repo firmware. Đã có xác nhận thao tác đóng thực trong mô phỏng, bổ sung cho các lệnh DONG0° ở log trước. A36 không còn chỉ là “chưa thấy chuyển động” đối với thao tác đóng. Góc mở thực/chuỗi đầy đủ, dạng sóng, đo latency, DHT lỗi runtime và đầy đủ S5/260lượt vẫn chưa được xác nhận; không tự đánh tất cả pass. Còi đã nghe theo phản hồi trước đó sau tăngvolume0.5.

Commit lần này chỉ trong Git firmware; không bao gồm sửa DOCX hoặc tài liệu ngoài repo, không push. Có code local/FSM/DHT hold/LDR/servo, log gọn3s, chẩn đoán PWM, KB/guide/tests và bằng chứng tương ứng.

Kiểm tra trước commit28/10/2026: [build SUCCESS](evidence/precommit-build-2026-10-28.log), [wiring và10nhóm host tests PASS](evidence/precommit-host-test-2026-10-28.log). Log build đã chuẩn hóa khoảng trắng cuối dòng để kiểm tra diff, không thay kết quả. Không đưa.pio/.host-build vào commit.

### Giảm âm và sắp xếp sơ đồ ngày28/10/2026

Người dùng yêu cầu còi nhỏ hơn và dây gọn hơn. Đổi volume0.5→0.25, giữ mode và tần số; đồng bộ boot header. Bố trí cảm biến trái, ESP32 giữa, LCD/relay/servo phải, còi/LED dưới; thêm nhãn, tách đường nguồn ra biên và route vuông góc. Đỏ5V/cam3V3/đenGND, tímADC-PWM/xanh ládigital/xanh dươngI2C. So sánh netlist với commit04d3aca: giữ nguyên44cặp chân nối, tất cả GPIO và thuộc tính điện khác; không thay FSM hoặc ngưỡng. Static wiring pass. Đã xem preview route hình học nội bộ (không phải render Wokwi thật); cần reload simulator để xác nhận hiển thị thực.

### Dọn riêng bố cục theo yêu cầu chi tiết ngày28/10/2026

Lưu [baseline trước khi sửa](evidence/layout-cleanup-before-2026-10-28.json) và [bảng đầu nối gốc](evidence/layout-cleanup-connections-before-2026-10-28.md). Sắp lại input trái/controller giữa/output phải, DHT trái-dưới, ACK dưới-trái, relay xếp dọc, servo dưới-phải. Route ngang/dọc, nguồn5V/3V3/GND riêng; quy ước hiện tại: đỏ5V,hồng3V3,đenGND,camADC,xanh dươngDHT,xanh ládigital/PWM,tímI2C. Quy ước này thay phần màu ở ghi chú bố cục trước đó.

[Đối chiếu sau sửa](evidence/layout-cleanup-verification-2026-10-28.md):44/44 cặp đầu nối không đổi; mọi linh kiện và thuộc tính điện gốc giữ nguyên, chỉ thêm3nhãn chữ phân vùng. GPIO25 vẫnVAN theo source, không tự đổi thànhFan. Volume0.25 đã có trước lượt này và được giữ nguyên. Không sửa C++/FSM/GPIO/ngưỡng trong lượt này. Wiring staticPASS; preview hình học nội bộ không thay cho render Wokwi thực. Cần reload simulator để nghiệm thu hiển thị.

### Đầu vào nền yên lặng khi Start — 28/10/2026

Người dùng yêu cầu Start không tự hú còi. MQ-2 trong diagram trước đó khởi tạo400ppm, có thể tạo ADC vượt ngưỡng local ngay sau lần đọc đầu; mức giữa slider không phải mức an toàn của FSM. Đổi riêng gas.attrs.ppm400→10 để demo khởi động ở nền thấp. Giữ LDR100lux và DHT28°C/45%, không sửa ngưỡng1800/2800, hysteresis, dây/GPIO hoặc vô hiệu hóa còi. Chỉ thay đầu vào mô phỏng mặc định, không hiệu chuẩn ppm của firmware. Kiểm tra JSON chỉ khác đúng thuộc tính ppm và wiringPASS; chưa xác nhận runtime sau reload. Stop rồi Start mới nạp mặc định; restart MCU trong lượt mô phỏng đang chạy có thể vẫn giữ mức slider đã chỉnh. Nếu còn state chốt sau hạ đầu vào, an toàn3s rồi thả/nhấn ACK mới.

### Final readability-only pass — 28/10/2026

Lưu [baseline ngay trước lượt này](evidence/final-readability-before-2026-10-28.json), gồm gas10ppm và volume0.25. DHT chuyển hoàn toàn vào cột INPUT; STATUS/ALARM gom còi/đỏ/xanh; tách các lane điều khiển, kéo cụm relay/servo gần hơn và bỏ detour chữ nhật. Mỗi tín hiệu Pump/Fan/Servo ngắn hơn baseline theo cùng mô hình hình học. Nhãn Fan GPIO25 là alias hiển thị theo yêu cầu; idvalve và vai tròVAN trong firmware không đổi.

Đổi cách trình bày nguồn: 23đường cấp nguồn/GND dài được ẩn bằng màu dây rỗng của Wokwi; thay bằng chú thích net cục bộ tại từng nhóm/chân. Các kết nối vẫn có trong JSON, không dùng ký hiệu nguồn giả hay nối ngầm mới. Ghi rõ5V/VIN,3V3 vàGND; không gộp nguồn. Legend thành hộp chữ nhiều dòng. Ghi chú bố cục/nguồn ở các mục lịch sử trước đó được thay thế bởi cách trình bày này.

[Kiểm chứng cuối](evidence/final-readability-verification-2026-10-28.md):44/44cặp đầu nốiMATCH; mọi linh kiện và thuộc tính điện gốc giữ nguyên, các part thêm chỉ là chữ. WiringPASS, diffcheckPASS; không sửa firmware/ngưỡng/defaultgas trong lượt này. Preview hình học không có signal xuyên thân linh kiện theo hộp bao xấp xỉ; chưa thay cho render Wokwi thực. Stop/Start để nghiệm thu bố cục.

### Khôi phục điều hướng checklist — 28/10/2026

Người dùng hỏi bước tiếp theo và không thấy checklistS. Checklist cũ vẫn ở phần kế hoạch nhưng bị chìm dưới KB dài; thêm bảng tiến độS0–S9 và link trực tiếp ở đầu KB/README. Đồng bộ mô tảS3/S4/S5 với bằng chứng runtime đã nhận, không đánh PASS toàn bộ các ôL hoặc260lượt. Bước kế tiếp vẫn là hoàn tấtS5, sau đóS6MQTT/mock; chưa bắt đầu code mạng/AI.

### Bypass S5 và bắt đầu S6 R6 — 28/10/2026

Theo yêu cầu trực tiếp của người dùng: hoãnS5 để làmS6, không đợi local checklist hoàn tất và không giả lập đánhPASS. Triển khai networktask riêngcore0, ESP-MQTT SDK, queueRX4/telemetry1/event8, reconnect/backoff/subscription+SUBACK, UTC/NTP, strictparser256byte, TTL15s/future2s/replay, local+AI fusion và nguồn reasonmask256/512. GPIO/sơ đồ/defaultgas/còi không đổi. Chưa có model AI thật hoặc dashboard.

[Hướng dẫn S6](reference/s6-mqtt-contract.md) có contract chung Python/C++, brokerconfig ignoredsecrets, QoS theo từng chiều, retained delivery caveatMQTT3.1.1 và bước test bằngmock. CSVR6 có39cột, cộtmức23 đổi tênmerged_level và thêmlocal_rule_level/ai_level. Log/LCD hiển thịmạng/freshness; maxloopgap là phép đo vònglặp, không phải latency vậtlý.

BuildESP32, hostcore/parser/fusion/encoder/rollover, Pythonmockunit vàPC↔localhostbroker smokePASS. Không có bằng chứngESP32WokwiMQTT/reconnect/flood/latency lúc này; N02/N03/N05/N07/N08 chưa đóng đầy đủ. Các mục S5/13×20 chưa tự đổi sangPASS. Chưa commit/pushS6.

### Hoàn thiện phần mềm S7–S8, hoãn model thật — 28/10/2026

Người dùng muốn đi tớiS8 trước, model thay sau. Đã thêm adapter/replay/plugin và modelmanifest trống cóDEFERRED; công cụcapture, tracker/audit, một-lệnhsoftwarechecks và bộscenariohost. R7 đóngdấuidentity nguồn build vàboot_id trongtelemetry, thêmtrạngtháimạng/lệnhđầu ra đểthu bằngchứng. NTP chuyểnkhởitạo sauWi-Fi vàthêmserver dựphòng dựa trênlogUTC0; chưa khẳngđịnhfixruntime. Không đổiGPIO/diagram/ngưỡng/driver/FSM.

[Kiểm tra cuối](evidence/s7s8-final-checks-2026-10-28/report.json): buildESP32, core/parser/fusion/encoder,11unitPython, PC-brokerreplay/capture vàhost240PASS/20DEFERRED. Bảng260lượtnghiệmthu giữnguyênhash/NOT_RUN. TC11 ảnh/model thật, metrics, camera thực, mạng/latencyMCU vàS5 còn hoãn/chờ. S9/DOCX không làm trong lượt này. Không tự commit/push.

### Làm gọn workspace và điều hướng — 28/10/2026

Người dùng thấy cấu trúc rối và hỏi bước tiếp theo. ThêmPCCC.code-workspace chỉ mở repo firmware, ẩn generated/build/venv và thêm taskbuild/check; không xóa dữ liệu. Đưa hướng dẫnR5 sangdocs/archive, contractS6 sangdocs/reference, cập nhật linkMarkdown, thêmproject-map và điểm vàoREADME. Không dời source/test/tools, Git, Word hoặc bảng260lượt. Bước tiếp theo là một lượt capture/replay trênWokwi cólog; model thật/S5/nghiệmthu còn giữ trạng thái đã ghi.

### Kiểm chứng guide S7–S8 — 28/10/2026

Đã chạy lại build, host core, 11 unit Python, 240 scenario host PASS/20 DEFERRED, replay dry-run và broker localhost smoke. Bảng nghiệm thu vẫn 260 NOT_RUN. Guide bổ sung điều kiện nền, khoảng replay 5 giây, bảng đầu ra mong đợi và cách phân biệt PUBACK với ESP thực nhận. Xem [kết quả và giới hạn](evidence/guide-verification-2026-10-28/README.md). Wokwi trực tiếp chưa chạy được vì truy cập VS Code qua Computer Use timeout; không lấy kết quả host/mock thay bằng chứng mô phỏng.

### Model thật và chế độ quan sát local — 28/10/2026

Người dùng đã tạo môi trường AI, tải weights rabahdev/fire-smoke-yolov8n (revision 13017fe8af477c25f5298d168e2dfede4b000753), nạp đúng nhãn smoke/fire và thử ảnh/webcam. Phản hồi: fire 0,426; smoke 0,689/0,660; một ảnh khó không detection; tóc bị nhận nhầm smoke khoảng0,36. Đây là quan sát rời rạc, không phải metrics hoặc chốt chất lượng model. Không sao chép ảnh cá nhân vào repo/dataset.

Theo yêu cầu triển khai: thêm `tools/yolo_plugin.py` (lazy load, BGR, Prediction/None), `tools/ai_observe.py` (camera/ảnh/video, JSONL từngframe, terminal mỗi1s, S lưuảnh/Q thoát), requirements đã thử và [manifest](../models/fire-smoke-yolov8n.manifest.json). Observer không gửi MQTT. Giữ ngưỡng xem0,25/chọn0,8 theo firmware; confidence thấp, khôngbox hoặc suy luận≥15s không tạo nhãn bìnhthường. Không đổiGPIO/FSM/TTL/ACK. Chưa thêm lọc thời gian, chưa cho model điều khiểnWokwi. Đánhgiá model/dataset/licensephụthuộc/S7 và S8 vẫn chưa đóng.

Xem [hướng dẫn quan sát](ai-observation.md). Kiểm tra thay đổi này gồm unit tests cổng confidence/plugin và suy luận ảnh/video headless bằng weights local; camera GUI/ảnh S do người dùng chạy để xác nhận. Không gọi kết quả đó là đo realtime/độ chính xác hoặc nghiệmthu260lượt.

### Replay đến ESP nhưng bị TIMESTAMP — 28/10/2026

Log người dùng mới xác nhận WiFi/MQTT/Sub/UTC=1/1/1/1; sau replay, Nhan/loi/drop=0/4/0 và Ly do goi cuoi=TIMESTAMP. Inbound đã tới bước kiểm tra timestamp, không còn chỉ là thiếu bản tin do model dưới confidence. Capture ai-live-01 kết thúc trước replay: không dùng file này làm bằng chứng replay/FSM. Trong capture, PC trôi118,179s còn UTC ESP trôi31,978s; sai biệt thời gian lúc PC nhận telemetry tăng11,795→97,996s (bao gồm độ trễ truyền). Thời gian mô phỏng tiến chậm là vấn đề cần xử lý; UTC=1 hiện chỉ gate epoch tối thiểu, không bảo đảm đồng hồ còn khớp PC. Không tắt TTL/future/replay validation để che lỗi; chưa sửa timestamp hoặc firmware trong lượt chẩn đoán.

Local log còn chứng minh timeout tại62,61s, giảm MQ rồi ACK_SAFE tại68,79s và NORMAL sau đó; đây là lệnh trong log, không tự xác nhận cơ khí hoặc toànS5. Xem [bản chẩn đoán](evidence/s6-replay-timestamp-diagnosis-2026-10-28.json). Chưa đánh bất kỳ lượt nghiệmthu PASS. Bước tiếp theo là xử lý clock của luồng tích hợp Wokwi/PC và thu capture đồng thời replay, không yêu cầu kiểm thử chất lượng AI thêm.

### Chuyển miền thời gian PC→Wokwi, giữ UTC thật mặc định — 28/10/2026

Theo yêu cầu sửa lỗiTIMESTAMP: thêm `tools/wokwi_clock.py` và cờ `--wokwi-clock`/`--expected-firmware-id` trong publisher. Chỉ lấy mốc telemetry mới khôngretained, đúngfirmware/boot, modeSIMULATION và mạng/clockhợp lệ; lấy trước khi đọcframe, không ngoại suy theo tốc độ PC, không dùng lại cùngmốc đểgia hạnAI. Telemetryquá5sPC/đợiquá10s không gửi; nguồnquá15sPC không gửi; disconnectvôhiệumốc vàrestartdừngpublisher. LoggiữsourceUTC vàghiWOKWI_SIMULATED_UTC; capturethêmclockdomainkhai báo. Không thayfirmware/contract4trường/ngưỡng/TTL/futuretolerance/GPIO/FSM. Đây là thíchnghi môi trường môphỏng, không phải đồngbộUTC thật hoặc chứngminh timingphầncứng; TTLtrênESP vẫnlàgiây môphỏng. [Hướngdẫn vàhai lệnhchạy đồngthời](wokwi-clock.md). RuntimeWokwi saufixchờ người dùng xácnhận; không đóngnghiệmthu từmockfixture.

Kiểm chứng clockmapper: [report](evidence/wokwi-clock-checks-2026-10-28/report.json) vàlogcùngthưmục. 26unittestPythonPASS; hostASan/UBSanPASS với caUTC+98s bịreject, anchorđúngđượcaccept vàTTL/replay giữ nguyên; localhostbrokerPCfixture25%clock nhận2packetmapped vàunknownkhôngphát. Hashfirmwaresourcevàbảng260lượt khôngđổi. Chưa có lượtWokwisaufix; không tựđánhPASS nghiệmthu.

### Wokwi replay clock mapping: runtime evidence - 28/10/2026

[Trace and limitations](evidence/wokwi-replay-clock-2026-10-28/summary.json): R7-ff4ea6a0f5395c1c, boot a475d28744300a80; publisher 4 PUBACK + 1 unknown suppressed. ESP accepted 0->4, rejected stays 4 from the previous run. Local level 0 throughout AI-triggered sequence: NORMAL -> WARNING/AI_WARNING -> FIRE_SUPPRESSION/AI_DANGER -> RECOVERY/DANGER_CLEARED. Command telemetry matches buzzer/loads/door policy. This demonstrates inbound MQTT + fusion/FSM with REPLAY_MOCK and WOKWI_SIMULATED_UTC; not real-model accuracy, independent motion/audio evidence, post-replay ACK, reconnect/flood/physical latency or full S6/S8 acceptance. No formal260run entry updated. Next: safe ACK to NORMAL and optionally run real model plugin using the same explicit clock mode.

### Chẩn đoán gửi confidence thấp từ model thật — 28/10/2026

Theo yêu cầu tiếp tục khi plugin chỉ UNAVAILABLE: bổ sung opt-in `yolo_plugin:predict_raw`, giữ nguyên `predict`0,8 và observer. Raw ưu tiên dự đoán đủ0,8; nếu không có thì gửi phát hiện≥0,25 với confidence nguyên bản, không cóbox/stale không phát và không sinh binh_thuong. Publisher thêm cờlog meets_confidence_threshold, không thêmtrường vào schemaMQTT. ESP giữ luật sẵn có: nhậnconfidence0,36 thì AIlevel0; localdanger vẫn có quyền bật. Lưuý raw là chẩnđoán đườngtruyền: lowconfidence có thể thay AIlevelcao trướcđó bằng0 và đưa FSM sangRECOVERY theo luật hiện tại; không coi raw là giải pháp báo giả đã kiểm định. Không đổi firmware/GPIO/ngưỡng/TTL. [Cách chạy](ai-observation.md).

Raw confidence checks: [report](evidence/raw-confidence-checks-2026-10-28/report.json): 29 Python tests PASS, host ASan/UBSan PASS, localhost MQTT fixture preserves score0.36. Live camera-to-ESP raw mode still requires user run; no formal acceptance updated.

### Người dùng hoàn tất lượt thử model qua camera — 28/10/2026

Người dùng xác nhận đã test xong và yêu cầu chia commit. [Trích kết quả publisher](evidence/real-model-user-publish-2026-10-28.json): đã thấy nhãn lua với confidence khoảng0,466–0,753 và PUBACK khi đưa ảnh lửa vào camera; dưới ngưỡng0,8 nên chưa kỳ vọng kích FIRE từ các bản tin này. Đây là bằng chứng model thật→publisher→broker; chưa có capture/bộ đếm ESP tương ứng để tự kết luận nhận đủ hoặc hoàn tất AI/S8. Replay trước đã có trace ESP nhận4gói/chuyểnFSM. Giữ nguyên giới hạn về modelaccuracy, rawmode, simulationclock và nghiệmthu260lượt. Không đưa weights, ảnh cá nhân hay runs/ vào Git.

### Phần mềm chuẩn bị nghiệm thu, giữ báo cáo sau — 28/10/2026

Người dùng yêu cầu implement phần còn lại trước, chỉ đưa vào báo cáo sau nghiệmthu; xácnhận chưa códatasetgánnhãn. Triểnkhai dashboard Streamlit1.66.1/Paho/SQLite local chỉđọc, subscribe device telemetry/event/availability + AI result/status. Có stale/offline15sPC, identity/boot/retained/import/fixturechecks, giữ lịch sử riêng, biểu đồPCreceive và bảngnghiệmthu chỉđọc. DB/log ởruns, không đổi firmware/GPIO/FSM.

Publisher thêm ai/status metadata khôngretained vàLWT, tách model/backend/publisher/unknown/STOP/ERROR với controlpacket4trường. TemporalGate opt-in3frame/2sPC/maxgap5s chỉdùngplugin thường; không tựhạngưỡng, khôngphátpredictioncũ hoặcnormalgiả. Chưa đánhgiápolicy bằngdataset nên mặcđịnh tắt. Có côngcụ networkcases (negative/replay/retained/floodbounded), importcapture lịch sử, dataset audit chốnggroup/hashleak, image-level metrics giữunknown, trainingentrypoint cókiểmtra manifest/YAMLsplit, và packageZIP source/evidence/ledger portable khôngsecrets/runtime; Wordchưađụngtới.

[Điểm bắtđầu nghiệmthu](acceptance-ready.md), [dashboard](dashboard.md), [dữliệu AI](ai-evaluation.md). Build/core/41Python/host240PASS20DEFERRED/localhostbroker/UI/MQTT→SQLite đãchạy; kếtquảđầyđủ trong reportđợt này. Các lượt260thực, S5/S6mấtmạng/timing vàmodelmetrics/train vẫn chưa đượcđánhhoànthành. Không tả hoànthành đồán chỉ vì code/tooling đãcó. BáocáoDOCX/S9 chỉnhsửasau khi có kếtquả người dùng xácnhận.

Release checks: [full report](evidence/dashboard-release-checks-2026-10-28/report.json), [post-check UI adjustment](evidence/dashboard-release-checks-2026-10-28/post-ui-check.json). All seven software stages PASS; firmware source and formal ledger hashes unchanged. User still needs real dataset/metrics and remaining Wokwi acceptance; DOCX untouched.


## Quyết định 29/10/2026 — triển khai local theo .env

Người dùng chốt MQTT broker, AI model và dashboard trên Mac; broker ngoài cấu hình sau. `.env.example` vào Git, `.env` riêng bị ignore. Dashboard tự kết nối, bỏ sidebar host/port, có mục nâng cao chỉ đọc. Python CLI > exported env > .env > default local; ESP đọc cấu hình khi build, secrets.h cũ vẫn ưu tiên. AI local dùng YOLO gate hiện tại, replay phải chọn rõ, không đổi unknown thành bình thường. Remote AI qua MQTT contract có sẵn; HTTP adapter mới chưa triển khai.

- [x] Cấu hình PC dùng chung, firmware generated header, broker loopback và launcher AI Wokwi.
- [x] UI tự kết nối, vẫn tách broker online khỏi ESP telemetry mới.
- [ ] Nghiệm thu Wokwi → broker local → dashboard/AI với build cấu hình mới. Không chuyển kết quả R7 cũ thành PASS mới.
- [ ] Kiểm chứng broker ngoài/TLS và remote AI khi thực sự triển khai.

Hướng dẫn hiện tại: [local-setup](local-setup.md). Không đổi GPIO, FSM, ngưỡng hay thời gian an toàn; chưa cập nhật Word.

Kiểm chứng phần mềm cấu hình local: 7/7 stage PASS (43 Python tests, build ESP, core, synthetic, localhost broker, UI, dashboard broker). Model thật nạp/inference ảnh trống thành công; không mở camera. [Bằng chứng](evidence/local-config-2026-10-29/report.json). Wokwi runtime local và nghiệm thu chính thức vẫn chưa đánh PASS.

## Dashboard: tái tổ chức UI/UX ngày 29/10/2026

Yêu cầu: hiểu trạng thái nhanh, nối KPI với biểu đồ và truy nguyên timestamp/bản tin. Giữ Streamlit và collector, không thay firmware/GPIO/logic an toàn.

- [x] Tổng quan tách ESP trực tiếp, broker, AI và dữ liệu lịch sử; thẻ có đơn vị/nguồn/ID.
- [x] Nút thẻ mở đúng xu hướng; tooltip chính xác; đường ngưỡng đọc config.h, không suy lại FSM.
- [x] Khoảng lịch sử dùng chung cho chart/table/EVENT, chọn điểm theo record ID và xem JSON nguồn; CSV theo bộ lọc.
- [x] Bố cục responsive, kỹ thuật thu gọn, giữ tab AI/nghiệm thu và lệnh tải chỉ đọc.
- [ ] Nghiệm thu trực tiếp các hành vi cảnh báo sau khi nhóm mở lại Wokwi; kiểm thử UI không tự ghi PASS đồ án.

Giới hạn: không có timestamp đo riêng từng sensor trong MQTT; hiện lấy tối đa 2.000 snapshot/500 EVENT trong khoảng đã chọn, không tổng hợp. [Hướng dẫn dashboard](dashboard.md).

Kiểm chứng UI redesign: 46 Python tests PASS, UI AppTest PASS (rỗng và fixture riêng, bốn KPI/chart/source, metric navigation, time filter, chọn ID), smoke broker PASS. Trình duyệt 1440×1000 và 390×844, chọn điểm → bản ghi#98; mobile không có overflow ngang. [Bằng chứng](evidence/dashboard-redesign-2026-10-29/report.json). Chưa đo thời gian thao tác với người dùng thật hay chạy lại nghiệm thu Wokwi.

### Dashboard compact — refinement 29/10/2026

- Thẻ native Streamlit 138px desktop, toàn bộ thẻ chọn được và có selected state; bỏ nút “Xem xu hướng”.
- Metadata snapshot/live/history dùng header chung; nguồn/chi tiết trong expander.
- Sáu lệnh thiết bị thành một hàng badge tự wrap, phân biệt lệnh ghi nhận với phản hồi vật lý.
- Giữ focus_metric dùng chung card/selectbox/chart/table, giữ time range và KPI cuối; record selector tách theo sensor.
- Chỉ sửa UI, test và tài liệu; không đổi database, sensor/FSM/threshold hay ESP32.

Kiểm chứng compact UI: AppTest PASS cho bốn thẻ, đồng bộ hai chiều với bộ chọn, giữ time range, KPI không đổi theo lịch sử và record-ID; 9 test store/presentation PASS. Desktop đo 138px/thẻ và 36.3px cho dải badge (chưa tính chú thích). Kiểm tra 1440/1024/390px; mobile không tràn ngang. [Bằng chứng](evidence/dashboard-compact-2026-10-29/report.json).

### Thẻ gauge theo ảnh tham chiếu

Người dùng chọn dạng đồng hồ bán nguyệt cho properties. Đã áp dụng bốn gauge trong native button, cao160px desktop; giữ chọn sensor→chart→raw record. Thang gauge chỉ phục vụ hiển thị, không thay phép tính hay phân loại an toàn. Không thêm công tắc điều khiển bơm/van. UI AppTest và2test gauge (mất mẫu/ngoài thang không làm sai số đọc) PASS.

Kiểm tra trước commit ngày29/10: cả7stage PASS (buildESP, hostcore, Pythontools, synthetic scenarios, broker smoke, UI, dashboard broker). [Báo cáo snapshot trước commit](evidence/pre-commit-checks-2026-10-29/report.json). Không tự ghi PASS nghiệm thu hoặc đánh giá model.
