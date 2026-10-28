#pragma once
#include <cstdint>
#include "sensors.h"

enum class SystemState { NORMAL, WARNING, FIRE_SUPPRESSION, RECOVERY };

// Bitmask giữ được nhiều nguyên nhân cùng lúc, không làm mất dấu nguồn kích hoạt.
enum TriggerReason : uint16_t {
  REASON_NONE = 0,
  REASON_SMOKE_WARNING = 1 << 0,
  REASON_SMOKE_DANGER = 1 << 1,
  REASON_FLAME = 1 << 2,
  REASON_TEMPERATURE = 1 << 3,
  REASON_TEMPERATURE_RATE = 1 << 4,
  REASON_DHT_FAULT = 1 << 5,
  REASON_FAST_FAULT = 1 << 6,
  REASON_LDR_FAULT = 1 << 7
};

struct SafetySnapshot {
  SystemState state = SystemState::NORMAL;
  SystemState previousState = SystemState::NORMAL;
  uint8_t dangerLevel = 0;
  uint16_t activeReasons = REASON_NONE;
  uint16_t latchedReasons = REASON_NONE;
  uint32_t stateEnteredMs = 0;
  bool suppressionLocked = false;
  bool ackReady = false;
  bool pumpOn = false;
  bool valveOn = false;
  bool buzzerOn = false;
  bool redLedOn = false;
  bool greenLedOn = true;
  bool thermalUnconfirmed = false;
  bool doorOpen = false;
  const char* transitionReason = "BOOT";
};

// Lõi thuần C++ để thử FSM bằng đồng hồ giả trên máy, không cần Arduino.
class SafetyController {
 public:
  bool update(const SensorSnapshot& sensors, uint32_t now);
  const SafetySnapshot& snapshot() const { return status_; }

 private:
  bool pressedEdge(bool raw, uint32_t now);
  uint8_t evaluate(const SensorSnapshot& sensors, uint32_t now);
  void transition(SystemState state, const char* reason, uint32_t now);
  void updateOutputs();
  SafetySnapshot status_;
  bool started_ = false;
  uint32_t startedMs_ = 0;
  bool smokeWarning_ = false;
  bool smokeDanger_ = false;
  bool temperatureDanger_ = false;
  bool temperatureRateDanger_ = false;
  bool safeTracking_ = false;
  uint32_t safeSinceMs_ = 0;
  bool ackInitialized_ = false;
  bool ackCandidate_ = false;
  bool ackStable_ = false;
  uint32_t ackCandidateSinceMs_ = 0;
};

const char* stateName(SystemState state);
const char* primaryReason(uint16_t reasons);
