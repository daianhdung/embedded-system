# Đối chiếu sau dọn bố cục — 28/10/2026

Chỉ sửa vị trí, tuyến/màu dây và chữ chú thích trong `diagram.json`. So sánh với bản working tree đã lưu **trước** lượt dọn này, không lấy HEAD làm bản gốc vì bản đang dùng đã có volume0.25.

| Component | Original ESP32 pin | New diagram pin | Status |
|---|---|---|---|
| MQ-2 AOUT | 35 | 35 | MATCH / unchanged |
| LDR AO | 32 | 32 | MATCH / unchanged |
| DHT22 DATA | 4 | 4 | MATCH / unchanged |
| ACK | 19 | 19 | MATCH / unchanged |
| LCD SDA / SCL | 21 / 22 | 21 / 22 | MATCH / unchanged |
| Relay BOM | 26 | 26 | MATCH / unchanged |
| Relay VAN | 25 | 25 | MATCH / unchanged |
| Servo PWM | 33 | 33 | MATCH / unchanged |
| Còi | 27 | 27 | MATCH / unchanged |
| LED đỏ (qua điện trở) | 14 | 14 | MATCH / unchanged |
| LED xanh (qua điện trở) | 13 | 13 | MATCH / unchanged |

- Giữ nguyên **44/44 cặp đầu nối**, tính cả Serial, điện trở, tải relay và pull-up DHT.
- Giữ nguyên VIN/5V, 3V3 và GND: không nhập hai đường cấp nguồn khác điện áp.
- Giữ tất cả linh kiện gốc và thuộc tính điện, giá trị điện trở, volume còi0.25; chỉ thêm3 nhãn vùng kiểu `wokwi-text`. Số part30→33; không thêm linh kiện điện.
- GPIO25 vẫn mang tên VAN theo source; từ “Fan” trong yêu cầu không được dùng để tự đổi chức năng.
- Trái: MQ-2/LDR/DHT22/ACK; giữa: ESP32; phải: LCD/relay/servo; dưới: còi/LED.
- Quy ước: đỏ5V, hồng3V3, đenGND, camADC, xanh dươngDATA DHT, xanh láđiều khiển/PWM, tímI2C. Các đường dây dùng đoạn ngang/dọc; nguồn đi theo các hành lang riêng.
- Kiểm tra tĩnh `python3 test/verify_wiring.py`: PASS. Không sửa code điều khiển trong lượt dọn này.
- Preview hình học nội bộ không phát hiện tuyến đi xuyên vùng thân linh kiện theo các hộp bao xấp xỉ. Đây **không phải ảnh render Wokwi**, không chứng minh toàn bộ nhãn/crossing trong giao diện thật đã hoàn hảo. Cần Stop rồi Start lại simulator để kiểm tra thực tế.

Bản trước: [JSON](layout-cleanup-before-2026-10-28.json), [bảng đầu nối trước](layout-cleanup-connections-before-2026-10-28.md). Source tuyến dây: [Wokwi diagram format](https://docs.wokwi.com/diagram-format).
