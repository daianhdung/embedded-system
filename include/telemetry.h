#pragma once
#include "sensors.h"

void printTelemetryHeader();
void printTelemetrySnapshot(const SensorSnapshot& snapshot, uint32_t now);
