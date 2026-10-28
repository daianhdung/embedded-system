# Kết nối trước khi dọn bố cục ngày28/10/2026

Nguồn: diagram.json hiện tại trong working tree, bao gồm âm lượng0.25; không lấy commit cũ thay cho bản đang dùng.

| Linh kiện/chân | Chân ESP32 gốc |
|---|---|
| gas:VCC | esp:VIN |
| gas:GND | esp:GND.1 |
| lcd:VCC | esp:VIN |
| lcd:GND | esp:GND.1 |
| pump:VCC | esp:VIN |
| pump:GND | esp:GND.1 |
| valve:VCC | esp:VIN |
| valve:GND | esp:GND.1 |
| dht:VCC | esp:3V3 |
| dht:GND | esp:GND.1 |
| dht:SDA | esp:D4 |
| gas:AOUT | esp:D35 |
| ack:1.l | esp:D19 |
| ack:2.l | esp:GND.1 |
| lcd:SDA | esp:D21 |
| lcd:SCL | esp:D22 |
| pump:IN | esp:D26 |
| valve:IN | esp:D25 |
| buzzer:2 | esp:D27 |
| buzzer:1 | esp:GND.1 |
| r_red:1 | esp:D14 |
| red:C | esp:GND.1 |
| r_green:1 | esp:D13 |
| green:C | esp:GND.1 |
| r_dht:1 | esp:3V3 |
| pump:COM | esp:3V3 |
| pump_load:C | esp:GND.1 |
| valve:COM | esp:3V3 |
| valve_load:C | esp:GND.1 |
| ldr:VCC | esp:3V3 |
| ldr:GND | esp:GND.1 |
| ldr:AO | esp:D32 |
| door:V+ | esp:VIN |
| door:GND | esp:GND.1 |
| door:PWM | esp:D33 |

Toàn bộ44cặp chân (gồm Serial và các liên kết điện trở/tải) được lưu trong layout-cleanup-before-2026-10-28.json để so sánh sau. GPIO25 là VAN trong source; không tự đổi thành FAN.
