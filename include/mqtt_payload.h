#pragma once
#include "network.h"
// Pure JSON encoder shared by device and host tests. Returns0 on overflow.
size_t encodeMqttSnapshot(const SensorSnapshot& sensors, const SafetySnapshot& safety,
                          const NetworkSnapshot& network, uint32_t uptimeMs,
                          uint32_t maxLoopGapMs, int64_t utcMs, uint32_t encodeMs,
                          bool event, char* buffer, size_t capacity);
