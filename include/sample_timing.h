#pragma once
#include <cmath>
#include <cstdint>

// Phép trừ unsigned vẫn đúng khi millis tràn sau khoảng 49,7 ngày.
inline bool isDue(uint32_t now, uint32_t previous, uint32_t interval) {
  return static_cast<uint32_t>(now - previous) >= interval;
}

// Chỉ ghép hai mẫu hợp lệ liên tiếp; lỗi đọc bắt đầu lại chuỗi.
struct TemperatureHistory {
  bool hasPrevious = false;
  float previousC = NAN;
  uint32_t previousMs = 0;

  float update(float currentC, uint32_t sampleMs, bool valid) {
    if (!valid || !std::isfinite(currentC)) {
      hasPrevious = false;
      return NAN;
    }
    float rate = NAN;
    const uint32_t elapsedMs = sampleMs - previousMs;
    if (hasPrevious && elapsedMs > 0) {
      rate = (currentC - previousC) * 1000.0f / elapsedMs;
    }
    previousC = currentC;
    previousMs = sampleMs;
    hasPrevious = true;
    return rate;
  }
};
