#include <cassert>
#include <cmath>
#include <cstdio>
#include <cstdint>
#include "safety.h"
#include "config.h"
#include "ldr_detector.h"
#include "servo_signal.h"

namespace {
SensorSnapshot healthy(uint32_t now) {
  SensorSnapshot s;
  s.fastValid = true;
  s.fastSampleMs = now;
  s.smokeAdc = 1000;
  s.ldrAdc = 2000; s.ldrValid = true; s.ldrSampleMs = now;
  s.dhtValid = s.dhtEverValid = true;
  s.dhtAttempts = 1;
  s.dhtSuccessMs = now;
  s.temperatureC = 28;
  s.humidityPct = 45;
  s.temperatureRateCps = 0;
  return s;
}

void normalAndThresholds() {
  SafetyController c;
  auto s = healthy(0);
  assert(!c.update(s, 0));
  assert(c.snapshot().greenLedOn && !c.snapshot().pumpOn && !c.snapshot().buzzerOn);
  s = healthy(100); s.smokeAdc = 1799; c.update(s, 100);
  assert(c.snapshot().dangerLevel == 0);
  s.smokeAdc = 1800; c.update(s, 100);
  assert(c.snapshot().state == SystemState::WARNING);
  assert(c.snapshot().redLedOn && c.snapshot().buzzerOn && !c.snapshot().pumpOn);
  s.smokeAdc = 1799; c.update(s, 100);
  assert(c.snapshot().dangerLevel == 1);
  s.smokeAdc = 1700; c.update(s, 100);
  assert(c.snapshot().dangerLevel == 1);
  s.smokeAdc = 1699; c.update(s, 100);
  assert(c.snapshot().dangerLevel == 0 && c.snapshot().state == SystemState::RECOVERY);
  assert(c.snapshot().redLedOn && !c.snapshot().buzzerOn);
  s.smokeAdc = 2799; c.update(s, 100);
  assert(c.snapshot().dangerLevel == 1);
  s.smokeAdc = 2800; c.update(s, 100);
  assert(c.snapshot().state == SystemState::FIRE_SUPPRESSION);
  assert(c.snapshot().pumpOn && c.snapshot().valveOn && c.snapshot().buzzerOn);
  s.smokeAdc = 2700; c.update(s, 100);
  assert(c.snapshot().dangerLevel == 2);
  s.smokeAdc = 2699; c.update(s, 100);
  assert(c.snapshot().dangerLevel == 1 && !c.snapshot().pumpOn);
  assert(c.snapshot().latchedReasons & REASON_SMOKE_DANGER);
  std::puts("PASS thresholds and smoke hysteresis at exact boundaries");
}

void independentDangerRules() {
  for (int input = 0; input < 4; ++input) {
    SafetyController c; c.update(healthy(0), 0);
    auto s = healthy(100);
    if (input == 0) s.flameDetected = true;
    if (input == 1) s.temperatureC = 55;
    if (input == 2) s.temperatureRateCps = 2;
    if (input == 3) s.smokeAdc = 2800;
    c.update(s, 100);
    assert(c.snapshot().dangerLevel == 2 && c.snapshot().pumpOn);
  }
  SafetyController c;
  auto s = healthy(0); s.temperatureC = 54.99f; s.temperatureRateCps = 1.999f;
  c.update(s, 0); assert(c.snapshot().dangerLevel == 0);
  s.temperatureC = 55; c.update(s, 0); assert(c.snapshot().pumpOn);
  s.temperatureC = 53; c.update(s, 0); assert(c.snapshot().dangerLevel == 2);
  s.temperatureC = 52.9f; c.update(s, 0); assert(!c.snapshot().pumpOn);
  s.temperatureRateCps = NAN; c.update(s, 0); assert(c.snapshot().dangerLevel == 0);
  std::puts("PASS independent flame, temperature, rise and smoke danger rules");
}

void faultsNeverDisableLocalFire() {
  SafetyController c;
  auto s = healthy(0); s.dhtValid = s.dhtEverValid = false; s.dhtAttempts = 0;
  c.update(s, 0); assert(c.snapshot().dangerLevel == 0);
  s.fastSampleMs = Config::kDhtStartupGraceMs - 1;
  s.ldrSampleMs = s.fastSampleMs;
  c.update(s, Config::kDhtStartupGraceMs - 1); assert(c.snapshot().dangerLevel == 0);
  s.fastSampleMs = Config::kDhtStartupGraceMs;
  s.ldrSampleMs = s.fastSampleMs;
  c.update(s, Config::kDhtStartupGraceMs);
  assert(c.snapshot().state == SystemState::WARNING);
  assert(c.snapshot().activeReasons & REASON_DHT_FAULT);
  s.flameDetected = true; c.update(s, Config::kDhtStartupGraceMs);
  assert(c.snapshot().pumpOn);
  s.flameDetected = false; s.smokeAdc = 2800;
  c.update(s, Config::kDhtStartupGraceMs); assert(c.snapshot().pumpOn);
  SafetyController stale; stale.update(healthy(0), 0);
  auto old = healthy(6501); old.dhtSuccessMs = 0;
  stale.update(old, 6501); assert(stale.snapshot().activeReasons & REASON_DHT_FAULT);
  SafetyController invalid; auto bad = healthy(0); bad.temperatureC = NAN;
  invalid.update(bad, 0); assert(invalid.snapshot().dangerLevel == 1);
  SafetyController fastFault; auto missing = healthy(0); missing.fastValid = false;
  fastFault.update(missing, 0); assert(fastFault.snapshot().activeReasons & REASON_FAST_FAULT);
  std::puts("PASS startup grace, invalid/stale sensor warning, local danger with failed DHT");
}

void recoveryRequiresNewDebouncedAck() {
  SafetyController c; c.update(healthy(0), 0);
  auto s = healthy(100); s.flameDetected = true; c.update(s, 100);
  c.update(healthy(200), 200);
  assert(c.snapshot().state == SystemState::RECOVERY && c.snapshot().redLedOn);
  s = healthy(220); s.ackPressedRaw = true; c.update(s, 220);
  s = healthy(240); c.update(s, 240);
  s = healthy(260); s.ackPressedRaw = true; c.update(s, 260);
  s = healthy(320); s.ackPressedRaw = true; c.update(s, 320);
  // Nhấn sớm không được tích lũy thành lệnh ACK khi giữ đến lúc an toàn.
  s = healthy(3500); s.ackPressedRaw = true; c.update(s, 3500);
  assert(c.snapshot().state == SystemState::RECOVERY && c.snapshot().ackReady);
  c.update(healthy(3600), 3600); c.update(healthy(3660), 3660);
  s = healthy(3700); s.ackPressedRaw = true; c.update(s, 3700);
  assert(c.snapshot().state == SystemState::RECOVERY);
  s = healthy(3750); s.ackPressedRaw = true; c.update(s, 3750);
  assert(c.snapshot().state == SystemState::NORMAL);
  assert(c.snapshot().greenLedOn && !c.snapshot().redLedOn);
  assert(c.snapshot().latchedReasons == REASON_NONE);
  std::puts("PASS RECOVERY latch, bounce, safe delay, held button and fresh ACK");
}

void timeoutLocksPumpUntilSafeAck() {
  SafetyController c; c.update(healthy(0), 0);
  auto fire = healthy(100); fire.flameDetected = true; c.update(fire, 100);
  fire = healthy(60099); fire.flameDetected = true; c.update(fire, 60099);
  assert(c.snapshot().pumpOn);
  fire = healthy(60100); fire.flameDetected = true; c.update(fire, 60100);
  assert(!c.snapshot().pumpOn && c.snapshot().suppressionLocked);
  assert(c.snapshot().state == SystemState::RECOVERY && c.snapshot().redLedOn);
  fire = healthy(60200); fire.flameDetected = true; fire.ackPressedRaw = true; c.update(fire, 60200);
  fire = healthy(120200); fire.flameDetected = true; fire.ackPressedRaw = true; c.update(fire, 120200);
  assert(c.snapshot().suppressionLocked && !c.snapshot().pumpOn);
  auto safe = healthy(120300); safe.ackPressedRaw = true; c.update(safe, 120300);
  safe = healthy(123301); safe.ackPressedRaw = true; c.update(safe, 123301);
  assert(c.snapshot().state == SystemState::RECOVERY);
  c.update(healthy(123400), 123400); c.update(healthy(123460), 123460);
  safe = healthy(123500); safe.ackPressedRaw = true; c.update(safe, 123500);
  safe = healthy(123560); safe.ackPressedRaw = true; c.update(safe, 123560);
  assert(c.snapshot().state == SystemState::NORMAL && !c.snapshot().suppressionLocked);
  fire = healthy(123600); fire.flameDetected = true; c.update(fire, 123600);
  assert(c.snapshot().pumpOn);
  std::puts("PASS 60s boundary, long persistent danger lockout and manual re-arm");
}

void newFireAndRollover() {
  SafetyController c; c.update(healthy(0), 0);
  auto s = healthy(100); s.flameDetected = true; c.update(s, 100);
  c.update(healthy(200), 200);
  s = healthy(300); s.flameDetected = true; c.update(s, 300);
  assert(c.snapshot().pumpOn && c.snapshot().stateEnteredMs == 300);
  SafetyController wrap; wrap.update(healthy(0xfffff000u), 0xfffff000u);
  const uint32_t start = 0xffffff00u;
  s = healthy(start); s.flameDetected = true; wrap.update(s, start);
  const uint32_t end = start + Config::kSuppressionMaxMs;
  s = healthy(end); s.flameDetected = true; wrap.update(s, end);
  assert(wrap.snapshot().suppressionLocked && !wrap.snapshot().pumpOn);
  std::puts("PASS new fire after early stop and millis rollover at suppression timeout");
}

void heldAtBootAndCombinedReasons() {
  SafetyController c;
  auto s = healthy(0); s.ackPressedRaw = true; c.update(s, 0);
  s = healthy(100); s.flameDetected = true; s.smokeAdc = 2800;
  s.ackPressedRaw = true; c.update(s, 100);
  assert((c.snapshot().activeReasons & REASON_FLAME) &&
         (c.snapshot().activeReasons & REASON_SMOKE_DANGER));
  s = healthy(200); s.ackPressedRaw = true; c.update(s, 200);
  s = healthy(4000); s.ackPressedRaw = true; c.update(s, 4000);
  assert(c.snapshot().state == SystemState::RECOVERY && c.snapshot().redLedOn);
  // Hết DHT trong RECOVERY phải chặn ACK, không được coi là đã an toàn.
  s = healthy(4100); s.dhtValid = false; c.update(s, 4100);
  assert(!c.snapshot().ackReady);
  assert(c.snapshot().latchedReasons & REASON_FLAME);
  std::puts("PASS held-at-boot ACK, simultaneous sources and sensor fault blocking ACK");
}

void thermalHazardSurvivesMissingData() {
  for (int rateOnly = 0; rateOnly < 2; ++rateOnly) {
    for (int stale = 0; stale < 2; ++stale) {
      SafetyController c; c.update(healthy(0), 0);
      auto hot = healthy(100);
      if (rateOnly) hot.temperatureRateCps = 3;
      else hot.temperatureC = 60;
      c.update(hot, 100);
      const uint16_t cause = rateOnly ? REASON_TEMPERATURE_RATE : REASON_TEMPERATURE;
      const uint32_t failedAt = stale ? 7000 : 3100;
      auto failed = healthy(failedAt);
      if (stale) failed.dhtSuccessMs = 100;
      else { failed.dhtValid = false; failed.temperatureC = NAN; failed.temperatureRateCps = NAN; }
      c.update(failed, failedAt);
      assert(c.snapshot().pumpOn && c.snapshot().dangerLevel == 2);
      assert(c.snapshot().activeReasons & cause);
      assert(c.snapshot().thermalUnconfirmed);
      assert(c.snapshot().activeReasons & REASON_DHT_FAULT);
      assert(!c.snapshot().ackReady);
      // Sau lỗi, mẫu đầu chưa có rate không được xóa chốt rate nguy hiểm.
      auto first = healthy(failedAt + 100); first.temperatureRateCps = NAN;
      c.update(first, failedAt + 100);
      if (rateOnly) assert(c.snapshot().pumpOn && c.snapshot().thermalUnconfirmed);
      auto recovered = healthy(failedAt + 3100);
      c.update(recovered, failedAt + 3100);
      assert(c.snapshot().state == SystemState::RECOVERY && !c.snapshot().pumpOn);
      assert(!c.snapshot().thermalUnconfirmed);
    }
  }
  SafetyController timed; timed.update(healthy(0), 0);
  auto hot = healthy(100); hot.temperatureC = 60; timed.update(hot, 100);
  auto failed = healthy(60100); failed.dhtValid = false;
  timed.update(failed, 60100);
  assert(timed.snapshot().suppressionLocked && !timed.snapshot().pumpOn);
  assert(timed.snapshot().dangerLevel == 2);
  failed = healthy(70100); failed.dhtValid = false; failed.ackPressedRaw = true;
  timed.update(failed, 70100); timed.update(failed, 70160);
  assert(!timed.snapshot().ackReady && !timed.snapshot().pumpOn);
  assert(timed.snapshot().activeReasons & REASON_TEMPERATURE);
  std::puts("PASS thermal high/rise survives failed/stale DHT, unknown recovery rate and timeout");
}

void lightAndDoorPolicy() {
  LdrDetector ldr;
  assert(!ldr.update(2000, true));
  assert(!ldr.update(501, true));
  assert(ldr.update(500, true));
  assert(ldr.update(749, true));
  assert(ldr.update(4096, false));
  assert(!ldr.update(750, true));
  assert(!ldr.update(-1, false));
  SafetyController c; c.update(healthy(0), 0);
  assert(!c.snapshot().doorOpen);
  auto warning = healthy(100); warning.smokeAdc = 1900; c.update(warning, 100);
  assert(!c.snapshot().doorOpen);
  c.update(healthy(200), 200);
  assert(c.snapshot().state == SystemState::RECOVERY && !c.snapshot().doorOpen);
  auto fire = healthy(300); fire.flameDetected = true; c.update(fire, 300);
  assert(c.snapshot().doorOpen && c.snapshot().pumpOn);
  fire = healthy(60300); fire.flameDetected = true; c.update(fire, 60300);
  assert(c.snapshot().doorOpen && !c.snapshot().pumpOn && c.snapshot().suppressionLocked);
  fire = healthy(60400); fire.flameDetected = true; fire.ackPressedRaw = true;
  c.update(fire, 60400); c.update(fire, 60460);
  assert(c.snapshot().doorOpen && !c.snapshot().ackReady);
  c.update(healthy(61000), 61000); c.update(healthy(61060), 61060);
  c.update(healthy(64060), 64060);
  auto ack = healthy(64100); ack.ackPressedRaw = true; c.update(ack, 64100);
  ack = healthy(64160); ack.ackPressedRaw = true; c.update(ack, 64160);
  assert(c.snapshot().state == SystemState::NORMAL && !c.snapshot().doorOpen);
  SafetyController early;
  fire = healthy(0); fire.flameDetected = true; early.update(fire, 0);
  early.update(healthy(100), 100);
  assert(early.snapshot().state == SystemState::RECOVERY && early.snapshot().doorOpen);
  SafetyController fault;
  auto failed = healthy(0); failed.ldrValid = false; fault.update(failed, 0);
  assert(fault.snapshot().activeReasons & REASON_LDR_FAULT);
  failed.flameDetected = true; failed.fastValid = false;
  fault.update(failed, 0); assert(fault.snapshot().pumpOn);
  SafetyController stale; auto old = healthy(1000); old.ldrSampleMs = 0;
  stale.update(old, 1000); assert(stale.snapshot().activeReasons & REASON_LDR_FAULT);
  assert(servoDutyForAngle(0) == 1638);
  assert(servoDutyForAngle(90) == 4915);
  assert(servoDutyForAngle(180) == 8192);
  assert(servoDutyForAngle(255) == servoDutyForAngle(180));
  std::puts("PASS LDR hysteresis/fault/independence, door warning/fire/recovery/timeout/ACK and servo pulse");
}

void randomizedInvariants() {
  SafetyController c;
  uint32_t random = 0x12345678;
  for (uint32_t i = 0; i < 20000; ++i) {
    random = random * 1664525u + 1013904223u;
    auto s = healthy(i * 20);
    s.smokeAdc = static_cast<int>((random >> 16) % 4096);
    s.flameDetected = (random & 0xff) == 0;
    s.ackPressedRaw = (random & 0x100) != 0;
    s.temperatureC = (random & 0x200) ? 28 : 56;
    if ((random & 0x3ff) == 0) s.dhtValid = false;
    c.update(s, i * 20);
    const auto& f = c.snapshot();
    assert(f.pumpOn == (f.state == SystemState::FIRE_SUPPRESSION));
    assert(f.valveOn == f.pumpOn);
    assert(!f.pumpOn || f.doorOpen);
    assert(f.state != SystemState::NORMAL || !f.doorOpen);
    assert(f.redLedOn == (f.state != SystemState::NORMAL));
    assert(f.greenLedOn == !f.redLedOn);
    assert(!f.suppressionLocked || !f.pumpOn);
    assert(!f.pumpOn || static_cast<uint32_t>(i * 20 - f.stateEnteredMs) < Config::kSuppressionMaxMs);
    assert(f.state != SystemState::NORMAL || f.dangerLevel == 0);
  }
  std::puts("PASS output/state invariants over 20000 deterministic synthetic steps");
}
}

int main() {
  normalAndThresholds(); independentDangerRules(); faultsNeverDisableLocalFire();
  recoveryRequiresNewDebouncedAck(); timeoutLocksPumpUntilSafeAck();
  newFireAndRollover(); heldAtBootAndCombinedReasons();
  thermalHazardSurvivesMissingData(); lightAndDoorPolicy(); randomizedInvariants();
}
