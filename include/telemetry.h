#pragma once
#include "sensors.h"
#include "safety.h"

void printTelemetryHeader();
void printTelemetrySnapshot(const SensorSnapshot& sensors, const SafetySnapshot& safety, uint32_t now);
void printStateEvent(const SensorSnapshot& sensors, const SafetySnapshot& safety, uint32_t now);
