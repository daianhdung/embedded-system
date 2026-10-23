#include "sensors.h"
#include <DHT.h>
#include "config.h"
#include "sample_timing.h"

namespace {
DHT dht(Config::kDhtPin, DHT22);
SensorSnapshot snapshot;
TemperatureHistory temperatureHistory;
uint32_t lastDhtAttemptMs = 0;
}

void beginSensors() {
  pinMode(Config::kSmokePin, INPUT);
  pinMode(Config::kFlamePin, INPUT_PULLUP);
  pinMode(Config::kAckPin, INPUT_PULLUP);
  analogReadResolution(12);
  analogSetPinAttenuation(Config::kSmokePin, ADC_11db);
  // Thích nghi DHT22 từ do_an_iot/src/main.cpp của nhóm (Giang Lê).
  // R4 trở về Adafruit sau khi DHTesp liên tục TIMEOUT trong test Wokwi.
  dht.begin();
  // Giữ DATA ở mức nghỉ HIGH; diagram có pull-up ngoài 10 kΩ lên 3,3 V.
  pinMode(Config::kDhtPin, INPUT_PULLUP);
  lastDhtAttemptMs = millis();
}

void sampleFastSensors(uint32_t now) {
  // Chỉ ghi ADC mô phỏng, chưa quy đổi ppm hay dùng luật báo cháy.
  snapshot.smokeAdc = analogRead(Config::kSmokePin);
  snapshot.flameDetected = digitalRead(Config::kFlamePin) == Config::kFlameActiveLevel;
  snapshot.ackPressedRaw = digitalRead(Config::kAckPin) == LOW;
  snapshot.fastSampleMs = now;
  snapshot.fastValid = true;
}

void pollDhtSensor(uint32_t now) {
  if (!isDue(now, lastDhtAttemptMs, Config::kDhtIntervalMs)) return;
  // Không bắt kịp bằng nhiều lần đọc dồn nếu vòng lặp bị trễ.
  snapshot.dhtIdleLevel = digitalRead(Config::kDhtPin);
  const uint32_t readStartedUs = micros();
  // Một giao dịch cho mỗi lịch 3 s; các getter sau dùng chung dữ liệu cache.
  const bool readSucceeded = dht.read();
  const float temperatureC = readSucceeded ? dht.readTemperature() : NAN;
  const float humidityPct = readSucceeded ? dht.readHumidity() : NAN;
  snapshot.dhtReadDurationUs = micros() - readStartedUs;
  // API Adafruit chỉ trả bool; không tự gán TIMEOUT/CHECKSUM khi chưa biết.
  snapshot.dhtStatus = readSucceeded ? "OK" : "READ_FAILED";
  const uint32_t sampleMs = millis();
  lastDhtAttemptMs = sampleMs;
  snapshot.dhtAttemptMs = sampleMs;
  ++snapshot.dhtAttempts;
  const bool valid = readSucceeded &&
      std::isfinite(temperatureC) && std::isfinite(humidityPct) &&
      temperatureC >= -40.0f && temperatureC <= 80.0f &&
      humidityPct >= 0.0f && humidityPct <= 100.0f;
  if (!valid && readSucceeded) snapshot.dhtStatus = "INVALID_VALUE";
  snapshot.dhtValid = valid;
  snapshot.temperatureC = valid ? temperatureC : NAN;
  snapshot.humidityPct = valid ? humidityPct : NAN;
  snapshot.temperatureRateCps = temperatureHistory.update(
      snapshot.temperatureC, sampleMs, valid);
  if (valid) {
    snapshot.dhtSuccessMs = sampleMs;
    snapshot.dhtEverValid = true;
  } else {
    ++snapshot.dhtErrors;
  }
}

const SensorSnapshot& sensorSnapshot() {
  return snapshot;
}
