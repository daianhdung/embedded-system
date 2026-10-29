# Bản đồ dự án: mở đâu, đọc đâu, chạy gì?

## 1. Mở đúng phạm vi làm việc

Thư mục môn học `HKVII_He-thong-nhung` có bài tập, dự án IoT cũ, tài liệu thầy và báo cáo Word. Đồ án đang làm ở `Nhom07-INT1461-PhongChayChuaChay`; repo Git hiện nằm bên trong thư mục `firmware`.

Trong VS Code, chọn **File → Open Workspace from File…**, mở `firmware/PCCC.code-workspace`. Workspace này chỉ hiển thị repo đang dùng và ẩn file build/môi trường sinh tự động. Có thể chạy **Terminal → Run Task → PCCC: Build ESP32** hoặc **PCCC: Kiểm tra phần mềm**. Workspace được tạo cho môi trường Mac hiện tại; đường dẫn PlatformIO dùng HOME của tài khoản.

Việc ẩn trong Explorer không xóa file. Wokwi vẫn đọc `.pio/build/esp32dev/firmware.bin` và ELF theo `wokwi.toml`.

## 2. Những thư mục trong workspace

```text
firmware/
├── README.md                 Bắt đầu ở đây
├── PCCC.code-workspace       Cửa sổ VSCode gọn cho dự án
├── src/                     Chương trình C++ chạy trên ESP32
├── include/                 Khai báo, kiểu dữ liệu và cấu hình C++
├── dashboard/               Giao diện Streamlit + subscriber + SQLite
├── tools/                   Chương trình Python chạy trên máy Mac/PC
├── test/                    Test phần mềm và dữ liệu kiểm tra
├── scripts/                 Hỗ trợ build, tạo mã phiên bản firmware
├── docs/
│   ├── KB.md                Checklist S0–S9 và các quyết định
│   ├── project-map.md       Bản đồ thư mục này
│   ├── s7-s8-guide.md       Hướng dẫn đang dùng để chạy/test
│   ├── reference/           Hợp đồng MQTT để tra cứu
│   ├── archive/             Hướng dẫn các bản cũ
│   └── evidence/            Bằng chứng, báo cáo và log đã chọn lưu
├── runs/                    Capture/report thô của những lần tự chạy
├── diagram.json             Linh kiện, chân nối và bố cục Wokwi
├── wokwi.toml               Chỉ đường cho Wokwi tới file đã build
└── platformio.ini           Board, framework, thư viện và cấu hình build
```

`runs/` xuất hiện sau khi chạy công cụ. Các thư mục `.pio`, `.host-build`, `.venv`, `.venv-ai` và `__pycache__` được ẩn trong workspace để giảm nhiễu. File dữ liệu vẫn tồn tại và các lệnh vẫn dùng được.

## 3. Bạn cần đọc file nào?

| Bạn muốn làm gì? | Bắt đầu tại đâu? |
|---|---|
| Mở giao diện giám sát | [Dashboard](dashboard.md), `dashboard/app.py` |
| Chuẩn bị nghiệm thu bản cuối | [Acceptance](acceptance-ready.md) |
| Audit/evaluate/train dữ liệu AI | [AI evaluation](ai-evaluation.md) |
| Xem đang ở bước S nào | [KB](KB.md#progress) |
| Chạy và kiểm tra bản hiện tại | [Hướng dẫn S7–S8](s7-s8-guide.md) |
| Hiểu chương trình bắt đầu và lặp thế nào | `src/main.cpp` |
| Xem GPIO, ngưỡng và lịch đọc | `include/config.h` |
| Hiểu đọc cảm biến | `src/sensors.cpp` |
| Hiểu điều kiện báo động, state, ACK, timeout | `src/safety.cpp` |
| Hiểu còi, relay và servo được điều khiển thế nào | `src/outputs.cpp` |
| Hiểu nhận AI qua MQTT và kiểm tra bản tin | `src/network.cpp`, `src/ai_contract.cpp` |
| Hiểu dữ liệu hiện trên LCD/log | `src/display.cpp`, `src/telemetry.cpp`, `src/mqtt_payload.cpp` |
| Quan sát model thật, không MQTT | `tools/ai_observe.py`, [hướng dẫn](ai-observation.md) |
| Plugin model YOLO lửa/khói | `tools/yolo_plugin.py` |
| Thử nguồn AI tạm thời từ PC | `tools/ai_publish.py` |
| Thu minh chứng khi chạy | `tools/capture_mqtt.py` |
| Xem/ghi bảng nghiệm thu | `tools/s8_track.py` |

Cặp `include/*.h` và `src/*.cpp` thường cùng một module: `.h` khai báo giao diện/kiểu, `.cpp` triển khai. Python trong `tools/` chạy trên PC, không được nạp vào ESP32. `test/` chạy trên máy để kiểm tra code, không phải vòng điều khiển của ESP32. Model thử nghiệm có weights local trong `models/` (Gitignore); xem hướng dẫn quan sát. Luồng nghiệm thu MQTT/model thật chưa hoàn tất.

## 4. Những gì nằm ngoài repo firmware

| Vị trí | Vai trò |
|---|---|
| `../docs/` | Phân tích/thiết kế/review cũ ở mức toàn đồ án; tra cứu khi cần, trạng thái hiện tại lấy từ KB |
| `../tests/integration-results.csv` | Bảng 260 lượt nghiệm thu gốc, công cụ S8 vẫn dùng bảng này |
| `../tests/` còn lại | Test và artifact giai đoạn đầu; test hiện tại nằm trong `firmware/test/` |
| `../config/` | Ghi chú cấu hình giai đoạn đầu; cấu hình đang chạy nằm trong `firmware/include/` |
| `../../do_an_iot/` | Source IoT cũ dùng làm tham khảo, không phải firmware hiện tại |
| Các file Word ở thư mục môn học | Hướng dẫn/báo cáo; S9 chưa sửa/đóng gói |

Chưa chuyểnGit hoặc các file Word/bảng nghiệm thu. Khi đóng gói S9 cần gom các tài liệu ngoài repo có chủ đích; không tạo bản nghiệm thu PASS song song.

## 5. Bước tiếp theo: nghiệm thu bản tích hợp

1. Mở [dashboard](dashboard.md), nhấn Kết nối và phân biệt live/stale.
2. Dùng [hướng dẫn nghiệm thu](acceptance-ready.md), chạy capture và nguồn AI đồng thời. Replay đã có trace nhận4gói/chuyểnFSM, không cần lặp lại chỉ để hiểu thư mục.
3. Ghi các ca local/mạng/AI còn thiếu vào ledger gốc bằng minh chứng thực.
4. Nhóm chưa có dataset: dùng [công cụ chuẩn bị/đánh giá](ai-evaluation.md) khi có dữ liệu. Không tự điền metrics hoặc train bằng ảnh chưa xác minh nhãn/nguồn.
5. Sau nghiệm thu mới đồng bộ Word và dùng `tools/package_submission.py` để đóng gói.

Nguồn cấu hình workspace: [VSCode workspaces](https://code.visualstudio.com/docs/editing/workspaces/workspaces), [workspace settings](https://code.visualstudio.com/docs/configure/settings).
