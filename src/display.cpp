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
  writeLine(0, "LOCAL R5 LDR+CUA");
  writeLine(1, "DHT: WAIT 3s");
}

void updateDisplay(const SensorSnapshot& s, const SafetySnapshot& f, uint32_t now) {
  char line[40];
  const char* state = "BINH THUONG";
  switch (f.state) {
    case SystemState::NORMAL: state = "BINH THUONG"; break;
    case SystemState::WARNING: state = "CANH BAO"; break;
    case SystemState::FIRE_SUPPRESSION: state = "CHUA CHAY"; break;
    case SystemState::RECOVERY: state = "KHOI PHUC"; break;
  }
  // Dòng đầu luôn giữ trạng thái và lệnh cửa; các trang dưới đổi dữ liệu.
  snprintf(line, sizeof(line), "%s C:%d", state, f.doorOpen);
  writeLine(0, line);
  const uint32_t page = (now / 2000) % 4;
  if (page == 0) {
    snprintf(line, sizeof(line), "S:%4d B%d V%d", s.smokeAdc, f.pumpOn, f.valveOn);
  } else if (page == 1) {
    snprintf(line, sizeof(line), "L:%4d F%d SIM", s.ldrAdc, s.flameDetected);
  } else if (page == 2) {
    if (s.dhtValid) snprintf(line, sizeof(line), "T:%5.1f H:%5.1f", s.temperatureC, s.humidityPct);
    else snprintf(line, sizeof(line), "DHT:%s", s.dhtAttempts == 0 ? "WAIT" : "ERROR");
  } else if (f.state == SystemState::RECOVERY) {
    snprintf(line, sizeof(line), "%s", f.ackReady ? "AN TOAN:NHAN ACK" :
        (f.suppressionLocked ? "TIMEOUT! CHO ACK" : "CHO AN TOAN 3s"));
  } else {
    snprintf(line, sizeof(line), "LOCAL:%s", primaryReason(f.activeReasons));
  }
  writeLine(1, line);
}
