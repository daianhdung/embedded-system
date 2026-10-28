#pragma once
#include "safety.h"

void beginOutputs();
void applyOutputs(const SafetySnapshot& safety);

// Readback cấu hình LEDC, không phải đo sóng chân GPIO hoặc feedback tải.
struct OutputDiagnostics {
  uint32_t buzzerHz;
  uint32_t servoHz;
  uint32_t servoDuty;
};
OutputDiagnostics outputDiagnostics();
