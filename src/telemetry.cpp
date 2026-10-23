#include "telemetry.h"
#include <cstdio>
#include <cstdarg>
#include <cstring>
#include <cmath>
#include "config.h"

namespace {

void printCsvHeader() {
  Serial.println("uptime_ms,smoke_adc,flame,temperature_c,humidity_pct,temp_rate_c_s,fast_valid,fast_sample_ms,dht_valid,dht_attempt_ms,dht_age_ms,dht_attempts,dht_errors,ack_raw,state,trigger_source,relay_pump,relay_valve,mode");
}

void printCsvSnapshot(const SensorSnapshot& s, uint32_t now) {
  char age[16];
  if (s.dhtEverValid) {
    snprintf(age, sizeof(age), "%lu", static_cast<unsigned long>(now - s.dhtSuccessMs));
  } else {
    snprintf(age, sizeof(age), "-1");
  }
  // NaN trong CSV biểu thị chưa có mẫu/lỗi; không giả số 0 là phép đo thật.
  char row[384];
  snprintf(row, sizeof(row),
      "%lu,%d,%d,%.2f,%.2f,%.3f,%d,%lu,%d,%lu,%s,%lu,%lu,%d,PHASE1,NONE,0,0,SIMULATION",
      static_cast<unsigned long>(now), s.smokeAdc, s.flameDetected,
      s.temperatureC, s.humidityPct, s.temperatureRateCps, s.fastValid,
      static_cast<unsigned long>(s.fastSampleMs), s.dhtValid,
      static_cast<unsigned long>(s.dhtAttemptMs), age,
      static_cast<unsigned long>(s.dhtAttempts), static_cast<unsigned long>(s.dhtErrors),
      s.ackPressedRaw);
  Serial.println(row);
}

bool includesCsv() {
  return Config::kSerialLogFormat != Config::SerialLogFormat::Readable;
}

bool includesReadable() {
  return Config::kSerialLogFormat != Config::SerialLogFormat::Csv;
}

// println phát CRLF: xuống dòng và đưa con trỏ về cột đầu terminal.
// Không dùng printf với LF đơn vì Wokwi có thể hiển thị thành bậc thang.
void printLogLine(const char* format, ...) {
  char line[192];
  va_list args;
  va_start(args, format);
  vsnprintf(line, sizeof(line), format, args);
  va_end(args);
  Serial.println(line);
}

void printReadableSnapshot(const SensorSnapshot& s, uint32_t now) {
  Serial.println();
  printLogLine("--- %.2f giay | PHASE 1 ---", now / 1000.0);
  if (s.fastValid) {
    printLogLine("  Khoi (ADC)  : %d / 4095", s.smokeAdc);
    printLogLine("  Lua gia lap : %s", s.flameDetected ? "PHAT HIEN" : "Khong phat hien");
    printLogLine("  Nut ACK     : %s", s.ackPressedRaw ? "Dang nhan" : "Da tha");
  } else {
    Serial.println("  Khoi/lua/ACK: Chua co mau");
  }
  if (s.dhtValid) {
    Serial.println("  DHT22       : OK");
    printLogLine("  Nhiet do    : %.1f C", s.temperatureC);
    printLogLine("  Do am       : %.1f %%", s.humidityPct);
    if (std::isfinite(s.temperatureRateCps)) {
      printLogLine("  Tang nhiet  : %.3f C/s", s.temperatureRateCps);
    } else {
      Serial.println("  Tang nhiet  : Cho du 2 mau hop le");
    }
    printLogLine("  Tuoi mau DHT: %.2f giay", (now - s.dhtSuccessMs) / 1000.0);
  } else {
    printLogLine("  DHT22       : %s", s.dhtStatus);
    if (s.dhtAttempts > 0) {
      printLogLine("  DATA GPIO%u : %s truoc khi doc", Config::kDhtPin,
          s.dhtIdleLevel == HIGH ? "HIGH" : "LOW");
      printLogLine("  Thoi gian doc: %lu us", static_cast<unsigned long>(s.dhtReadDurationUs));
      if (strcmp(s.dhtStatus, "TIMEOUT") == 0) {
        Serial.println("  Chi tiet    : Khong nhan du xung phan hoi DHT");
      } else if (strcmp(s.dhtStatus, "READ_FAILED") == 0) {
        Serial.println("  Chi tiet    : Driver chua doc duoc goi DHT hop le");
      } else if (strcmp(s.dhtStatus, "CHECKSUM") == 0) {
        Serial.println("  Chi tiet    : Nhan duoc xung nhung checksum sai");
      }
    }
    Serial.println("  Nhiet do/am : Chua co du lieu hop le");
    if (s.dhtEverValid) {
      printLogLine("  Mau tot cu  : Cach day %.2f giay", (now - s.dhtSuccessMs) / 1000.0);
    }
  }
  printLogLine("  Lan doc DHT : %lu | Loi: %lu",
      static_cast<unsigned long>(s.dhtAttempts), static_cast<unsigned long>(s.dhtErrors));
}
}  // Kết thúc các hàm nội bộ của phần ghi log.

void printTelemetryHeader() {
  if (includesReadable()) {
    Serial.println("=== PHASE 1 R4: DHT Adafruit 1.4.7 ===");
    printLogLine("Lich: khoi/lua %lu ms | DHT22 %lu ms | log %lu ms",
        static_cast<unsigned long>(Config::kSensorIntervalMs),
        static_cast<unsigned long>(Config::kDhtIntervalMs),
        static_cast<unsigned long>(Config::kLogIntervalMs));
    Serial.println("Khoi la ADC mo phong, chua hieu chuan ppm.");
    Serial.println("AI/FSM chua trien khai. Lenh bom/van giu TAT.");
    Serial.println("Chua co phan hoi tiep diem relay.");
    Serial.println("Neu DHT loi: kiem tra day DATA, nguon va GND.");
  }
  if (includesCsv()) printCsvHeader();
}

void printTelemetrySnapshot(const SensorSnapshot& snapshot, uint32_t now) {
  if (includesReadable()) printReadableSnapshot(snapshot, now);
  if (includesCsv()) printCsvSnapshot(snapshot, now);
}
