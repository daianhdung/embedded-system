#pragma once
#include "sensors.h"

void beginDisplay();
void updateDisplay(const SensorSnapshot& snapshot, uint32_t now);
