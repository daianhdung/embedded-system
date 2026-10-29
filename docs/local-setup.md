# Chạy local mặc định — quyết định ngày 29/10/2026

MQTT broker, model AI và dashboard chạy trên Mac. Wokwi ESP32 truy cập broker qua gateway của extension VS Code. Đây là triển khai dữ liệu local, chưa phải hệ thống hoạt động hoàn toàn không có Internet: Wokwi và đồng bộ NTP hiện vẫn có thể cần Internet.

## Khởi động

Mở terminal tại thư mục `firmware`. Máy hiện tại đã có `.env` local. Máy mới sao chép `.env.example` thành `.env` (không ghi đè cấu hình riêng đang có), cài `.venv/bin/python -m pip install -r tools/requirements-local.txt`; AI dùng `.venv-ai` và `tools/requirements-ai.txt` như hướng dẫn trước.

1. Terminal 1: `.venv/bin/python tools/local_broker.py`. Giữ terminal mở. Broker chỉ nghe `127.0.0.1:1883`, dùng cho phát triển, không có tài khoản hay lưu bền bản tin. Dừng bằng Ctrl+C.
2. Build: `~/.platformio/penv/bin/pio run`. Stop/Start Wokwi trong VS Code để nạp firmware mới. Đọc firmware ID mới trên boot; ID thay đổi khi cấu hình triển khai thay đổi. Broker của ESP là `host.wokwi.internal:1883`.
3. Terminal 2: `.venv/bin/python -m streamlit run dashboard/app.py --server.address 127.0.0.1 --server.port 8501 --server.headless true --browser.gatherUsageStats false`. Mở http://127.0.0.1:8501; tự kết nối. Không còn sidebar nhập cấu hình. “Máy chủ dữ liệu đã kết nối” chưa có nghĩa ESP đang gửi dữ liệu.
4. Terminal 3, sau khi ESP đã kết nối và có telemetry mới: `.venv-ai/bin/python tools/start_ai.py --interval 1`. Lệnh đọc `.env`, lấy ID build hiện tại và bật ánh xạ giờ Wokwi. Camera sẽ mở khi chính bạn chạy lệnh. Dừng bằng Ctrl+C. Không có phát hiện hợp lệ → UNAVAILABLE, không tự phát nhãn bình thường. Nếu model báo confidence thấp thì vẫn giữ gate hiện tại; việc đổi sang local không sửa chất lượng model.

Có thể dùng VS Code Run Task: **PCCC: MQTT local**, **PCCC: Dashboard**, **PCCC: AI local (Wokwi)**. Tránh chạy thêm broker nếu cổng1883 đã có broker đang hoạt động.

Capture là tùy chọn: `.venv/bin/python tools/capture_mqtt.py --out runs/local-01.jsonl --duration 120 --ai-backend MODEL_UNVERIFIED --ai-clock-domain WOKWI_SIMULATED_UTC`. Chạy ở terminal khác đồng thời publisher nếu cần minh chứng. CLI này cũng đọc broker/prefix từ `.env`.

## Cấu hình

Thứ tự ưu tiên Python: cờ CLI > biến môi trường đã export > `.env` > mặc định local. `.env` hỗ trợ KEY=value, dấu nháy và comment; không thực thi shell, không nội suy `$VAR`. Đường dẫn model tương đối được tính từ repo, không từ terminal đang mở. Sau khi sửa `.env`, khởi động lại Python services; sửa MQTT URI/prefix/tài khoản cho ESP cần build và restart Wokwi.

| Biến | Dùng để làm gì |
|---|---|
| PCCC_MQTT_HOST / PORT | Broker cho dashboard, AI, capture, mock |
| PCCC_ESP_MQTT_URI | Broker cho ESP, ví dụ mqtt://host.wokwi.internal:1883 |
| PCCC_TOPIC_PREFIX | Cùng một nhóm topic cho ESP và PC |
| PCCC_MQTT_USERNAME / PASSWORD | Tài khoản broker ngoài; không hiển thị trên UI |
| PCCC_MQTT_TLS | 1 dùng TLS với CA hệ thống cho các MQTT client Python; đổi PORT tương ứng |
| PCCC_AI_BACKEND | local (YOLO), plugin (adapter Python có sẵn), replay (mock chọn rõ) |
| PCCC_AI_PLUGIN | Hàm module:function khi dùng backend plugin; remote HTTP cần adapter riêng |
| PCCC_AI_MODEL_PATH / MODEL_ID | Weights và tên model để theo dõi nguồn |
| PCCC_AI_SOURCE / DEVICE | Camera/video và thiết bị tính toán, mặc định 0 / cpu |
| PCCC_AI_CONFIDENCE | Gate của model trên PC; ESP vẫn có gate độc lập0.8 |
| PCCC_EXPECTED_FIRMWARE_ID | Tùy chọn khóa dashboard/publisher vào đúng firmware |

`include/secrets.h` cũ, nếu có, vẫn ưu tiên cho ESP để không phá cấu hình riêng. Nên chuyển cấu hình sang `.env` rồi bỏ các override trùng trong secrets.h để tránh lệch PC/ESP. Build chỉ ghi header vào `.pio/generated`, không in mật khẩu. `.env`, secrets.h và runtime data không đưa vào Git/gói bàn giao.

Backend local luôn chọn YOLO `predict` có gate; backend plugin mới dùng PCCC_AI_PLUGIN để tránh vô tình chọn raw diagnostics. `ai_publish.py --backend replay` là lựa chọn mock tường minh; các hướng dẫn cũ dựa vào replay mặc định phải thêm cờ này.

## Chuyển ra ngoài khi cần

Đổi HOST/PORT/TOPIC và tài khoản; ESP dùng URI tương ứng. Với TLS, Python dùng PCCC_MQTT_TLS=1; cấu hình CA cho ESP cần được kiểm chứng riêng, không bỏ qua xác minh chứng chỉ. Không công khai broker local ẩn danh này ra Internet. AI có thể chuyển lên máy khác và gửi cùng MQTT contract; dịch vụ HTTP mới cần adapter chứ không chỉ nhập URL. Dùng ESP thật: `start_ai.py --hardware`, URI trỏ IP LAN hoặc broker ngoài, không dùng host.wokwi.internal.

Không thay GPIO, đấu dây, luật cảm biến, ACK, timeout hay FSM. Bằng chứng R7 cũ vẫn là lịch sử, chưa chứng minh firmware cấu hình local mới đã nghiệm thu. Gói ZIP cũ ngày28/10 là snapshot cũ; cần tạo gói mới trước bàn giao.

Nguồn: [Wokwi VS Code gateway](https://docs.wokwi.com/vscode/project-config), [host.wokwi.internal](https://docs.wokwi.com/guides/esp32-wifi#connecting-to-your-local-machine).
