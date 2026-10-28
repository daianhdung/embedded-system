#pragma once
#include <cstdint>
#include "config.h"

// Xung mô phỏng 500..2500 us cho 0..180 độ, chu kỳ 20 ms.
// Trả duty cho LEDC16 bit; tách phép đổi để test không cần Arduino.
inline uint32_t servoDutyForAngle(uint8_t angle) {
  const uint32_t bounded = angle > 180 ? 180 : angle;
  const uint32_t pulseUs = Config::kServoMinPulseUs +
      bounded * (Config::kServoMaxPulseUs - Config::kServoMinPulseUs) / 180;
  return static_cast<uint32_t>((static_cast<uint64_t>(pulseUs) *
      (1UL << Config::kServoResolutionBits)) / (1000000UL / Config::kServoFrequencyHz));
}
