#pragma once
#include "config.h"

// Module Wokwi mắc chia áp: sáng tăng => ADC giảm. Chỉ là lửa giả lập.
// Mất mẫu không tự xóa sự kiện đã phát hiện; caller báo validity riêng.
class LdrDetector {
 public:
  bool update(int adc, bool valid) {
    if (valid && adc >= 0 && adc <= 4095) {
      if (adc <= Config::kLdrFireAdc) detected_ = true;
      else if (adc >= Config::kLdrClearAdc) detected_ = false;
    }
    return detected_;
  }
 private:
  bool detected_ = false;
};
