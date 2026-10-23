#pragma once
#include <Arduino.h>

struct SensorSnapshot {
  int smokeAdc = 0;
  bool flameDetected = false;
  bool ackPressedRaw = false;
  bool fastValid = false;
  float temperatureC = NAN;
  float humidityPct = NAN;
  float temperatureRateCps = NAN;
  bool dhtValid = false;
  const char* dhtStatus = "WAIT";
  int dhtIdleLevel = -1;
  uint32_t dhtReadDurationUs = 0;
  bool dhtEverValid = false;
  uint32_t fastSampleMs = 0;
  uint32_t dhtAttemptMs = 0;
  uint32_t dhtSuccessMs = 0;
  uint32_t dhtAttempts = 0;
  uint32_t dhtErrors = 0;
};

void beginSensors();
void sampleFastSensors(uint32_t now);
void pollDhtSensor(uint32_t now);
const SensorSnapshot& sensorSnapshot();
