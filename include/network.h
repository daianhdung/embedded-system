#pragma once
#include "ai_contract.h"
#include "safety.h"
struct NetworkSnapshot {
  bool enabled = false;
  bool taskStarted = false;
  bool wifi = false;
  bool mqtt = false;
  bool subscribed = false;
  bool clock = false;
  char bootId[17] = {};
  AiSignal ai;
  AiReject lastReject = AiReject::None;
  uint32_t accepted = 0;
  uint32_t rejected = 0;
  uint32_t rxDropped = 0;
  uint32_t eventsDropped = 0;
  uint32_t publishFailed = 0;
};
// Called by local loop: only zero-wait queue operations, no sockets/JSON/DNS.
void beginNetwork();
const NetworkSnapshot& pollNetwork();
uint32_t maxObservedLocalLoopGap();
void sendNetworkSnapshot(const SensorSnapshot& sensors, const SafetySnapshot& safety,
                         uint32_t now, uint32_t maxLoopGapMs, bool event);
