#include "safety.h"
#include <cmath>
#include "config.h"

const char* stateName(SystemState state) {
  switch (state) {
    case SystemState::NORMAL: return "NORMAL";
    case SystemState::WARNING: return "WARNING";
    case SystemState::FIRE_SUPPRESSION: return "FIRE_SUPPRESSION";
    case SystemState::RECOVERY: return "RECOVERY";
  }
  return "UNKNOWN";
}

const char* primaryReason(uint16_t reasons) {
  if (reasons & REASON_FLAME) return "FLAME";
  if (reasons & REASON_SMOKE_DANGER) return "SMOKE_DANGER";
  if (reasons & REASON_TEMPERATURE) return "TEMPERATURE";
  if (reasons & REASON_TEMPERATURE_RATE) return "TEMP_RISE";
  if (reasons & REASON_SMOKE_WARNING) return "SMOKE_WARNING";
  if (reasons & REASON_DHT_FAULT) return "DHT_FAULT";
  if (reasons & REASON_FAST_FAULT) return "FAST_FAULT";
  if (reasons & REASON_LDR_FAULT) return "LDR_FAULT";
  return "NONE";
}

bool SafetyController::pressedEdge(bool raw, uint32_t now) {
  if (!ackInitialized_) {
    // Giữ nút từ khi boot không được tính là một lần xác nhận mới.
    ackInitialized_ = true;
    ackCandidate_ = ackStable_ = raw;
    ackCandidateSinceMs_ = now;
    return false;
  }
  if (raw != ackCandidate_) {
    ackCandidate_ = raw;
    ackCandidateSinceMs_ = now;
  }
  if (ackCandidate_ != ackStable_ &&
      static_cast<uint32_t>(now - ackCandidateSinceMs_) >= Config::kAckDebounceMs) {
    ackStable_ = ackCandidate_;
    return ackStable_;
  }
  return false;
}

uint8_t SafetyController::evaluate(const SensorSnapshot& s, uint32_t now) {
  uint8_t level = 0;
  uint16_t reasons = REASON_NONE;
  if (s.fastValid) {
    // Ngưỡng lên giữ theo khung Phần F; ngưỡng xuống cách 100 ADC chống rung.
    if (s.smokeAdc >= Config::kSmokeWarningAdc) smokeWarning_ = true;
    else if (s.smokeAdc < Config::kSmokeWarningAdc - Config::kSmokeHysteresisAdc)
      smokeWarning_ = false;
    if (s.smokeAdc >= Config::kSmokeDangerAdc) smokeDanger_ = true;
    else if (s.smokeAdc < Config::kSmokeDangerAdc - Config::kSmokeHysteresisAdc)
      smokeDanger_ = false;
    if (smokeWarning_) { level = 1; reasons |= REASON_SMOKE_WARNING; }
    if (smokeDanger_) { level = 2; reasons |= REASON_SMOKE_DANGER; }
  }
  // LDR độc lập với tính hợp lệ của mẫu MQ; giữ cờ lửa khi mẫu LDR bị mất.
  if (s.flameDetected) { level = 2; reasons |= REASON_FLAME; }
  if (!s.ldrValid || static_cast<uint32_t>(now - s.ldrSampleMs) > Config::kLdrStaleMs) {
    if (level < 1) level = 1;
    reasons |= REASON_LDR_FAULT;
  }
  if (!s.fastValid || static_cast<uint32_t>(now - s.fastSampleMs) > Config::kFastStaleMs) {
    if (level < 1) level = 1;
    reasons |= REASON_FAST_FAULT;
  }
  const bool validDht = s.dhtValid && s.dhtEverValid &&
      std::isfinite(s.temperatureC) && std::isfinite(s.humidityPct) &&
      static_cast<uint32_t>(now - s.dhtSuccessMs) <= Config::kDhtStaleMs;
  if (validDht) {
    if (s.temperatureC >= Config::kTemperatureDangerC) temperatureDanger_ = true;
    else if (s.temperatureC < Config::kTemperatureClearC) temperatureDanger_ = false;
    // Rate NaN sau lỗi/chưa đủ cặp không chứng minh tốc độ đã giảm.
    if (std::isfinite(s.temperatureRateCps)) {
      temperatureRateDanger_ = s.temperatureRateCps >= Config::kTemperatureRateDangerCps;
    }
  } else if (s.dhtAttempts > 0 ||
             static_cast<uint32_t>(now - startedMs_) >= Config::kDhtStartupGraceMs) {
    // Lỗi DHT nâng lên cảnh báo; khói/lửa vẫn có quyền nâng lên chữa cháy.
    if (level < 1) level = 1;
    reasons |= REASON_DHT_FAULT;
  }
  // Chỉ mẫu hợp lệ mới giải trừ nguy hiểm nhiệt đã xác nhận.
  // Timeout vẫn dừng tải trong FSM, nhưng không xóa nguyên nhân hoặc cho ACK.
  if (temperatureDanger_) { level = 2; reasons |= REASON_TEMPERATURE; }
  if (temperatureRateDanger_) { level = 2; reasons |= REASON_TEMPERATURE_RATE; }
  status_.thermalUnconfirmed = (temperatureDanger_ || temperatureRateDanger_) &&
      (!validDht || (temperatureRateDanger_ && !std::isfinite(s.temperatureRateCps)));
  status_.activeReasons = reasons;
  return level;
}

void SafetyController::transition(SystemState state, const char* reason, uint32_t now) {
  status_.previousState = status_.state;
  status_.state = state;
  status_.stateEnteredMs = now;
  status_.transitionReason = reason;
}

bool SafetyController::update(const SensorSnapshot& s, uint32_t now) {
  if (!started_) {
    started_ = true;
    startedMs_ = now;
    status_.stateEnteredMs = now;
  }
  const bool ackEdge = pressedEdge(s.ackPressedRaw, now);
  const SystemState before = status_.state;
  status_.dangerLevel = evaluate(s, now);
  if (status_.dangerLevel == 0) {
    if (!safeTracking_) { safeTracking_ = true; safeSinceMs_ = now; }
  } else {
    safeTracking_ = false;
  }
  status_.ackReady = safeTracking_ &&
      static_cast<uint32_t>(now - safeSinceMs_) >= Config::kSafeBeforeAckMs;
  // Giữ nguyên các nguyên nhân của lượt báo động, kể cả khi đầu vào đã an toàn.
  if (status_.dangerLevel > 0) status_.latchedReasons |= status_.activeReasons;
  switch (status_.state) {
    case SystemState::NORMAL:
      if (status_.dangerLevel == 2) transition(SystemState::FIRE_SUPPRESSION, "LOCAL_DANGER", now);
      else if (status_.dangerLevel == 1) transition(SystemState::WARNING, "LOCAL_WARNING", now);
      break;
    case SystemState::WARNING:
      if (status_.dangerLevel == 2) transition(SystemState::FIRE_SUPPRESSION, "LOCAL_DANGER", now);
      else if (status_.dangerLevel == 0) transition(SystemState::RECOVERY, "HAZARD_CLEARED", now);
      break;
    case SystemState::FIRE_SUPPRESSION:
      // Ưu tiên hạn tối đa, kể cả khi điều kiện vừa hạ ngay tại mốc hết hạn.
      if (static_cast<uint32_t>(now - status_.stateEnteredMs) >= Config::kSuppressionMaxMs) {
        status_.suppressionLocked = true;
        transition(SystemState::RECOVERY, "MAX_DURATION", now);
      } else if (status_.dangerLevel < 2) {
        transition(SystemState::RECOVERY, "DANGER_CLEARED", now);
      }
      break;
    case SystemState::RECOVERY:
      if (status_.dangerLevel == 2 && !status_.suppressionLocked) {
        // Một nguy hiểm mới vẫn kích được chữa cháy nếu lượt trước chưa chạm hạn.
        transition(SystemState::FIRE_SUPPRESSION, "NEW_LOCAL_DANGER", now);
      } else if (status_.ackReady && ackEdge) {
        status_.suppressionLocked = false;
        status_.latchedReasons = REASON_NONE;
        transition(SystemState::NORMAL, "ACK_SAFE", now);
      }
      break;
  }
  updateOutputs();
  return before != status_.state;
}

void SafetyController::updateOutputs() {
  // Cửa chỉ mở vì FIRE, không tự mở vì WARNING; giữ tới ACK về NORMAL.
  if (status_.state == SystemState::FIRE_SUPPRESSION) status_.doorOpen = true;
  else if (status_.state == SystemState::NORMAL) status_.doorOpen = false;
  status_.pumpOn = status_.valveOn = status_.state == SystemState::FIRE_SUPPRESSION;
  status_.buzzerOn = status_.state == SystemState::WARNING || status_.pumpOn;
  status_.redLedOn = status_.state != SystemState::NORMAL;
  status_.greenLedOn = status_.state == SystemState::NORMAL;
}
