#include "display.h"
#include <LiquidCrystal_I2C.h>
#include <Wire.h>
#include <cstdio>
#include <cstring>
#include "config.h"

namespace {
// Giữ API và địa chỉ LCD từ do_an_iot/src/main.cpp của nhóm (Giang Lê).
LiquidCrystal_I2C lcd(Config::kLcdAddress, 16, 2);

void writeLine(uint8_t row, const char* text) {
  char padded[17];
  memset(padded, ' ', 16);
  const size_t length = strlen(text);
  memcpy(padded, text, length < 16 ? length : 16);
  padded[16] = '\0';
  lcd.setCursor(0, row);
  lcd.print(padded);
}
}

void beginDisplay() {
  Wire.begin(Config::kSdaPin, Config::kSclPin);
  lcd.init();
  lcd.backlight();
  writeLine(0, "PHASE1 SENSORS");
  writeLine(1, "DHT: WAIT 3s");
}

void updateDisplay(const SensorSnapshot& s, uint32_t now) {
  char line[40];
  // LCD HD44780 mặc định không hỗ trợ đầy đủ tiếng Việt có dấu.
  if (s.dhtValid) {
    snprintf(line, sizeof(line), "T:%5.1f H:%5.1f", s.temperatureC, s.humidityPct);
  } else {
    snprintf(line, sizeof(line), "DHT:%s", s.dhtAttempts == 0 ? "WAIT" : "ERROR");
  }
  writeLine(0, line);
  // Cứ 4 giây hiện trang phụ 1 giây để thấy đây mới là pha đọc cảm biến.
  if ((now / 1000) % 4 == 3) {
    snprintf(line, sizeof(line), "P1 ACK:%d AI:N/A", s.ackPressedRaw);
  } else {
    snprintf(line, sizeof(line), "S:%4d F:%d SIM", s.smokeAdc, s.flameDetected);
  }
  writeLine(1, line);
}
