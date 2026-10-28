#include <Arduino.h>
#include "config.h"
#include "display.h"
#include "sample_timing.h"
#include "sensors.h"
#include "telemetry.h"
#include "safety.h"
#include "outputs.h"

namespace {
uint32_t lastFastMs = 0;
uint32_t lastLdrMs = 0;
uint32_t lastControlMs = 0;
uint32_t lastDisplayMs = 0;
uint32_t lastLogMs = 0;
SafetyController controller;
}

void setup() {
  // Giữ driver cảm biến/LCD Phase 1; thêm lớp luật độc lập với mọi kết nối mạng.
  beginOutputs();
  Serial.begin(Config::kSerialBaud);
  beginSensors();
  beginDisplay();
  const uint32_t now = millis();
  sampleFastSensors(now);
  sampleLdrSensor(now);
  lastLdrMs = now;
  lastFastMs = lastControlMs = lastDisplayMs = lastLogMs = now;
  const bool changed = controller.update(sensorSnapshot(), now);
  applyOutputs(controller.snapshot());
  printTelemetryHeader();
  if (changed) printStateEvent(sensorSnapshot(), controller.snapshot(), now);
  updateDisplay(sensorSnapshot(), controller.snapshot(), now);
  printTelemetrySnapshot(sensorSnapshot(), controller.snapshot(), now);
}

void loop() {
  uint32_t now = millis();
  if (isDue(now, lastControlMs, Config::kControlIntervalMs)) {
    sampleControlInputs();
    lastControlMs = now;
  }
  if (isDue(now, lastFastMs, Config::kSensorIntervalMs)) {
    sampleFastSensors(now);
    lastFastMs = now;
  }
  if (isDue(now, lastLdrMs, Config::kLdrIntervalMs)) {
    sampleLdrSensor(now);
    lastLdrMs = now;
  }
  pollDhtSensor(now);
  now = millis();
  const bool changed = controller.update(sensorSnapshot(), now);
  // Điều khiển tải trước LCD/log để thao tác hiển thị không nằm trước quyết định.
  applyOutputs(controller.snapshot());
  if (changed) printStateEvent(sensorSnapshot(), controller.snapshot(), now);
  if (changed || isDue(now, lastDisplayMs, Config::kDisplayIntervalMs)) {
    updateDisplay(sensorSnapshot(), controller.snapshot(), now);
    lastDisplayMs = now;
  }
  if (isDue(now, lastLogMs, Config::kLogIntervalMs)) {
    printTelemetrySnapshot(sensorSnapshot(), controller.snapshot(), now);
    lastLogMs = now;
  }
}
