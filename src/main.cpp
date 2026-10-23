#include <Arduino.h>
#include "config.h"
#include "display.h"
#include "sample_timing.h"
#include "sensors.h"
#include "telemetry.h"

namespace {
uint32_t lastFastMs = 0;
uint32_t lastDisplayMs = 0;
uint32_t lastLogMs = 0;

void initializeInactiveOutputs() {
  // Chỉ giữ tắt tải ở Phase 1; chưa có máy trạng thái hay chữa cháy.
  for (const uint8_t pin : {Config::kPumpRelayPin, Config::kValveRelayPin}) {
    digitalWrite(pin, Config::kRelayOffLevel);
    pinMode(pin, OUTPUT);
  }
  for (const uint8_t pin : {Config::kBuzzerPin, Config::kRedLedPin, Config::kGreenLedPin}) {
    digitalWrite(pin, LOW);
    pinMode(pin, OUTPUT);
  }
}
}

void setup() {
  // Tham khảo trình tự init của do_an_iot/src/main.cpp (nhóm, Giang Lê);
  // đổi chân theo Phần F; bỏ Wi-Fi/Blynk/servo và delay khởi động.
  initializeInactiveOutputs();
  Serial.begin(Config::kSerialBaud);
  beginSensors();
  beginDisplay();
  const uint32_t now = millis();
  sampleFastSensors(now);
  lastFastMs = lastDisplayMs = lastLogMs = now;
  printTelemetryHeader();
  printTelemetrySnapshot(sensorSnapshot(), now);
}

void loop() {
  uint32_t now = millis();
  if (isDue(now, lastFastMs, Config::kSensorIntervalMs)) {
    sampleFastSensors(now);
    lastFastMs = now;
  }
  pollDhtSensor(now);
  now = millis();
  if (isDue(now, lastDisplayMs, Config::kDisplayIntervalMs)) {
    updateDisplay(sensorSnapshot(), now);
    lastDisplayMs = now;
  }
  if (isDue(now, lastLogMs, Config::kLogIntervalMs)) {
    printTelemetrySnapshot(sensorSnapshot(), now);
    lastLogMs = now;
  }
}
