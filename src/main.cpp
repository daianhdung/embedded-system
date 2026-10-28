#include <Arduino.h>
#include "config.h"
#include "display.h"
#include "sample_timing.h"
#include "sensors.h"
#include "telemetry.h"
#include "safety.h"
#include "outputs.h"
#include "network.h"

namespace {
uint32_t lastFastMs = 0;
uint32_t lastLdrMs = 0;
uint32_t lastControlMs = 0;
uint32_t lastDisplayMs = 0;
uint32_t lastLogMs = 0;
uint32_t lastNetworkMs = 0, lastLoopMs = 0, maxLoopGapMs = 0;
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
  beginNetwork(); // start after local inputs/outputs are initialized; no network wait
  printTelemetryHeader();
  if (changed) printStateEvent(sensorSnapshot(), controller.snapshot(), now);
  updateDisplay(sensorSnapshot(), controller.snapshot(), now);
  printTelemetrySnapshot(sensorSnapshot(), controller.snapshot(), now);
  if (changed) sendNetworkSnapshot(sensorSnapshot(), controller.snapshot(), now, 0, true);
  lastLoopMs = millis();
}

void loop() {
  uint32_t now = millis();
  const uint32_t gap = now - lastLoopMs;
  if (gap > maxLoopGapMs) maxLoopGapMs = gap;
  lastLoopMs = now;
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
  const NetworkSnapshot& net = pollNetwork();
  now = millis(); // sample after queue copy: receipt must not be ahead of this tick
  AiSignal ai = net.ai;
  if (!net.clock || !net.subscribed) ai.received = false;
  const bool changed = controller.update(sensorSnapshot(), now, ai);
  // Điều khiển tải trước LCD/log để thao tác hiển thị không nằm trước quyết định.
  applyOutputs(controller.snapshot());
  if (changed) {
    printStateEvent(sensorSnapshot(), controller.snapshot(), now);
    sendNetworkSnapshot(sensorSnapshot(), controller.snapshot(), now, maxLoopGapMs, true);
  }
  if (isDue(now, lastNetworkMs, 1000)) {
    sendNetworkSnapshot(sensorSnapshot(), controller.snapshot(), now, maxLoopGapMs, false);
    lastNetworkMs = now;
  }
  if (changed || isDue(now, lastDisplayMs, Config::kDisplayIntervalMs)) {
    updateDisplay(sensorSnapshot(), controller.snapshot(), now);
    lastDisplayMs = now;
  }
  if (isDue(now, lastLogMs, Config::kLogIntervalMs)) {
    printTelemetrySnapshot(sensorSnapshot(), controller.snapshot(), now);
    lastLogMs = now;
  }
}
