#pragma once
#include "sensors.h"
#include "safety.h"

void beginDisplay();
void updateDisplay(const SensorSnapshot& sensors, const SafetySnapshot& safety, uint32_t now);
