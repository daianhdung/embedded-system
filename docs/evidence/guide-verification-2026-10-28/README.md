# Kiểm chứng guide S7–S8 — 28/10/2026

Đã đối chiếu guide với CLI Python, replay mẫu, telemetry và FSM hiện tại. Lượt này chỉ bổ sung tài liệu, không thay đổi code firmware.

| Hạng mục | Kết quả | Phạm vi |
|---|---|---|
| `.venv/bin/python tools/verify_project.py --out runs/guide-verification-2026-10-28` | PASS | Build ESP32, host core, 11 unit Python, scenario host |
| Scenario host | 240 PASS / 0 FAIL / 20 DEFERRED | Dữ liệu và đồng hồ giả; không phải Wokwi |
| `ai_publish.py --dry-run --interval 0.1` | PASS | 4 packet hợp lệ, 1 unknown không publish; không MQTT |
| `/tmp/pccc-s6-tools/bin/python test/broker_smoke.py` | PASS | Broker localhost thật; kiểm tra mock/watch, replay có unknown và capture có PC fixture |
| TCP tới broker.hivemq.com:1883 | Kết nối được | Chỉ TCP; không chứng minh MQTT/UTC/ESP hoạt động |
| `s8_track.py status` | 260 NOT_RUN | Không ghi kết quả giả vào bảng nghiệm thu |
| Wokwi trong VS Code | NOT_RUN | Công cụ Computer Use chọn VS Code timeout sau 20 giây; không đọc được trạng thái mô phỏng. Máy không có `wokwi-cli` trên PATH |
| Camera/model thật | DEFERRED | Giữ theo yêu cầu thay model sau |

Report và log của lượt kiểm tra phần mềm được lưu cùng thư mục này: [report.json](report.json). Report gốc ghi đường dẫn chạy trong `runs/`; các log đi kèm được sao chép nguyên byte. Kết quả smoke và dry-run ở bảng trên là ghi nhận từ đầu ra lệnh trong phiên làm việc, không có transcript riêng trong thư mục này.

Các chỉnh sửa guide: nêu điều kiện nền và topic, tăng khoảng replay từ 2 lên 5 giây để dễ quan sát, thêm bảng trạng thái/đầu ra/ACK, phân biệt CAPTURE ready và PUBACK với việc ESP thực sự nhận bản tin, thêm cách chẩn đoán lỗi.

Phần còn lại để xác minh guide từ đầu đến cuối: chạy Wokwi, thu capture có identity ESP thật, đối chiếu EVENT và đầu ra nhìn/nghe được theo bảng ở mục 3 của guide. Chưa đánh dấu bất kỳ ca nghiệm thu nào PASS.
