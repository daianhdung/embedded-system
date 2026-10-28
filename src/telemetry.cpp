#include "telemetry.h"
#include <Arduino.h>
#include <cstdio>
#include <cstdarg>
#include <cmath>
#include <cstring>
#include "config.h"
#include "outputs.h"
#include "network.h"
#include "network_config.h"
#include "firmware_identity.h"

namespace {
bool includesCsv() { return Config::kSerialLogFormat != Config::SerialLogFormat::Readable; }
bool includesReadable() { return Config::kSerialLogFormat != Config::SerialLogFormat::Csv; }

// println phát CRLF; không dùng LF đơn làm con trỏ trôi sang phải trên Wokwi.
void printLine(const char* format, ...) __attribute__((format(printf, 1, 2)));
void printLine(const char* format, ...) {
  char line[224];
  va_list args;
  va_start(args, format);
  vsnprintf(line, sizeof(line), format, args);
  va_end(args);
  Serial.println(line);
}

const char* sourceName(const SafetySnapshot& safety) {
  return triggerSource(safety.latchedReasons);
}

void printCsvSnapshot(const SensorSnapshot& s, const SafetySnapshot& f, uint32_t now,
                      const char* recordType) {
  char age[16];
  if (s.dhtEverValid) snprintf(age, sizeof(age), "%lu", static_cast<unsigned long>(now - s.dhtSuccessMs));
  else snprintf(age, sizeof(age), "-1");
  const char* eventSource = (strcmp(recordType, "EVENT") == 0 &&
      f.state == SystemState::NORMAL && f.previousState == SystemState::RECOVERY)
      ? "OPERATOR" : sourceName(f);
  // Giữ 19 cột đầu Phase 1; nối thêm dữ liệu luật/FSM. Không đưa NaN vào JSON về sau.
  char row[896];
  snprintf(row, sizeof(row),
      "%lu,%d,%d,%.2f,%.2f,%.3f,%d,%lu,%d,%lu,%s,%lu,%lu,%d,%s,%s,%d,%d,SIMULATION,%s,%s,%s,%u,%u,%u,%d,%d,%d,%d,%d,%d,%d,%lu,%lu,%d,%u,%d,%u,%u",
      static_cast<unsigned long>(now), s.smokeAdc, s.flameDetected,
      s.temperatureC, s.humidityPct, s.temperatureRateCps, s.fastValid,
      static_cast<unsigned long>(s.fastSampleMs), s.dhtValid,
      static_cast<unsigned long>(s.dhtAttemptMs), age,
      static_cast<unsigned long>(s.dhtAttempts), static_cast<unsigned long>(s.dhtErrors),
      s.ackPressedRaw, stateName(f.state), eventSource, f.pumpOn, f.valveOn,
      recordType, stateName(f.previousState), f.transitionReason,
      static_cast<unsigned int>(f.dangerLevel), static_cast<unsigned int>(f.activeReasons),
      static_cast<unsigned int>(f.latchedReasons), f.suppressionLocked, f.ackReady,
      f.buzzerOn, f.redLedOn, f.greenLedOn, s.ldrAdc, s.ldrValid,
      static_cast<unsigned long>(s.ldrSampleMs),
      static_cast<unsigned long>(now - s.ldrSampleMs), f.doorOpen,
      static_cast<unsigned int>(f.doorOpen ? Config::kDoorOpenAngle : Config::kDoorClosedAngle),
      f.thermalUnconfirmed, static_cast<unsigned int>(f.localLevel),
      static_cast<unsigned int>(f.aiLevel));
  Serial.println(row);
}
}

void printTelemetryHeader() {
  if (includesReadable()) {
    Serial.println("=== S7/S8 R7: LOCAL + MQTT + PLUGGABLE AI / TEST TOOLS ===");
    printLine("Firmware: %s", firmwareIdentity());
    printLine("Khoi: canh bao >=%d, nguy hiem >=%d ADC", Config::kSmokeWarningAdc, Config::kSmokeDangerAdc);
    printLine("Nhiet: >=%.1f C hoac tang >=%.1f C/s", Config::kTemperatureDangerC, Config::kTemperatureRateDangerCps);
    printLine("Bom toi da %lu s; an toan %lu s roi NHAN ACK MOI",
        static_cast<unsigned long>(Config::kSuppressionMaxMs / 1000),
        static_cast<unsigned long>(Config::kSafeBeforeAckMs / 1000));
    printLine("MQ: %lu ms | ACK: %lu ms | DHT: %lu ms",
        static_cast<unsigned long>(Config::kSensorIntervalMs),
        static_cast<unsigned long>(Config::kControlIntervalMs),
        static_cast<unsigned long>(Config::kDhtIntervalMs));
    printLine("LDR GPIO%u: %lu ms; ADC <=%d: LUA GIA, >=%d: HET LUA GIA",
        static_cast<unsigned int>(Config::kLdrPin), static_cast<unsigned long>(Config::kLdrIntervalMs),
        Config::kLdrFireAdc, Config::kLdrClearAdc);
    printLine("Cua GPIO%u: DONG %u do / MO %u do; PWM %lu Hz, kenh%u (coi kenh%u)",
        static_cast<unsigned int>(Config::kDoorServoPin), static_cast<unsigned int>(Config::kDoorClosedAngle),
        static_cast<unsigned int>(Config::kDoorOpenAngle), static_cast<unsigned long>(Config::kServoFrequencyHz),
        static_cast<unsigned int>(Config::kServoChannel), static_cast<unsigned int>(Config::kBuzzerChannel));
    Serial.println("SIMULATION: ADC chua hieu chuan ppm; LDR khong phai cam bien lua IR; MQTT da co; AI chi la contract/mock, chua co model.");
    printLine("MQTT: %s | AI topic: %s", NetworkConfig::kEnabled ? "ENABLED" : "DISABLED", NetworkConfig::kAiTopic);
    Serial.println("Relay npn: HIGH=BAT. Den tai BOM/VAN qua COM-NO.");
    printLine("Log gon: moi %lu ms | EVENT in ngay | Muc: 0=an toan,1=canh bao,2=nguy hiem",
        static_cast<unsigned long>(Config::kLogIntervalMs));
    Serial.println("Cua/relay tren log la LENH, chua co feedback vi tri/tai.");
    Serial.println("AUDIO DIAG: volume Wokwi 0.25; PWM readback khong phai do song GPIO.");
  }
  if (includesCsv()) {
    Serial.println("uptime_ms,smoke_adc,flame,temperature_c,humidity_pct,temp_rate_c_s,fast_valid,fast_sample_ms,dht_valid,dht_attempt_ms,dht_age_ms,dht_attempts,dht_errors,ack_raw,state,trigger_source,relay_pump,relay_valve,mode,record_type,previous_state,transition_reason,merged_level,active_reason_mask,latched_reason_mask,suppression_locked,ack_ready,buzzer,red_led,green_led,ldr_adc,ldr_valid,ldr_sample_ms,ldr_age_ms,door_open,door_angle_cmd,thermal_unconfirmed,local_rule_level,ai_level");
  }
}

void printStateEvent(const SensorSnapshot& sensors, const SafetySnapshot& safety, uint32_t now) {
  if (includesReadable()) {
    printLine("[EVENT %.2f s] %s -> %s", now / 1000.0,
        stateName(safety.previousState), stateName(safety.state));
    const char* source = safety.state == SystemState::NORMAL ? "OPERATOR" : triggerSource(safety.latchedReasons);
    printLine("  Ly do: %s | Nguon: %s | Kich hoat: %s",
        safety.transitionReason, source, primaryReason(safety.latchedReasons));
  }
  if (includesCsv()) printCsvSnapshot(sensors, safety, now, "EVENT");
}

void printTelemetrySnapshot(const SensorSnapshot& s, const SafetySnapshot& f, uint32_t now) {
  if (includesReadable()) {
    Serial.println();
    printLine("--- %.2f s | %s | Muc %u ---", now / 1000.0,
        stateName(f.state), static_cast<unsigned int>(f.dangerLevel));
    printLine("  Hien tai: %s (mask=%u) | Chot: %s/%s",
        primaryReason(f.activeReasons), static_cast<unsigned int>(f.activeReasons),
        sourceName(f), primaryReason(f.latchedReasons));
    const NetworkSnapshot& n = pollNetwork();
    printLine("  Local/AI: %u/%u | WiFi/MQTT/Sub/UTC: %d/%d/%d/%d",
        static_cast<unsigned int>(f.localLevel), static_cast<unsigned int>(f.aiLevel),
        n.wifi, n.mqtt, n.subscribed, n.clock);
    printLine("  Task mang: %s | Max loop gap: %lu ms (khong phai latency cam bien)",
        n.taskStarted ? "ON" : "OFF", static_cast<unsigned long>(maxObservedLocalLoopGap()));
    printLine("  AI: %s | Nhan/loi/drop: %lu/%lu/%lu | Ly do goi cuoi: %s",
        n.subscribed && n.clock && n.ai.fresh(millis()) ? "FRESH (model hoac mock)" : "UNAVAILABLE",
        static_cast<unsigned long>(n.accepted), static_cast<unsigned long>(n.rejected),
        static_cast<unsigned long>(n.rxDropped), aiRejectName(n.lastReject));
    printLine("  Khoi ADC: %d/4095 | LDR ADC: %d/4095", s.smokeAdc, s.ldrAdc);
    printLine("  Lua gia: %s | LDR: %s | Tuoi: %lu ms",
        s.flameDetected ? "CO" : "KHONG", s.ldrValid ? "OK" : "LOI",
        static_cast<unsigned long>(now - s.ldrSampleMs));
    if (s.dhtValid) {
      char rate[24];
      if (std::isfinite(s.temperatureRateCps)) snprintf(rate, sizeof(rate), "%.3f C/s", s.temperatureRateCps);
      else snprintf(rate, sizeof(rate), "CHO 2 MAU TOT");
      printLine("  Nhiet: %.1f C | Am: %.1f %% | Tang: %s", s.temperatureC, s.humidityPct, rate);
      printLine("  DHT: OK | Doc/loi: %lu/%lu | Tuoi: %.2f s",
          static_cast<unsigned long>(s.dhtAttempts), static_cast<unsigned long>(s.dhtErrors),
          (now - s.dhtSuccessMs) / 1000.0);
    } else {
      printLine("  DHT: %s | Doc/loi: %lu/%lu", s.dhtStatus,
          static_cast<unsigned long>(s.dhtAttempts), static_cast<unsigned long>(s.dhtErrors));
    }
    printLine("  Bom/van: %s/%s | Coi: %s | Do/xanh: %s/%s",
        f.pumpOn ? "BAT" : "TAT", f.valveOn ? "BAT" : "TAT",
        f.buzzerOn ? "BAT" : "TAT", f.redLedOn ? "BAT" : "TAT", f.greenLedOn ? "BAT" : "TAT");
    printLine("  Cua (lenh): %s %u do | ACK: %s",
        f.doorOpen ? "MO" : "DONG", static_cast<unsigned int>(f.doorOpen ? Config::kDoorOpenAngle : Config::kDoorClosedAngle),
        s.ackPressedRaw ? "NHAN" : "THA");
    const OutputDiagnostics pwm = outputDiagnostics();
    printLine("  PWM doc lai: coi %lu Hz | cua %lu Hz | duty cua %lu/65536",
        static_cast<unsigned long>(pwm.buzzerHz), static_cast<unsigned long>(pwm.servoHz),
        static_cast<unsigned long>(pwm.servoDuty));
    if (f.thermalUnconfirmed) Serial.println("  GIU NGUY HIEM NHIET: cho mau tot; bom van gioi han 60s");
    if (f.state == SystemState::FIRE_SUPPRESSION) {
      printLine("  Bom da chay: %.1f/%.1f s", (now - f.stateEnteredMs) / 1000.0,
          Config::kSuppressionMaxMs / 1000.0);
    }
    if (f.state == SystemState::RECOVERY) {
      printLine("  Khoa timeout: %s | %s", f.suppressionLocked ? "CO" : "KHONG",
          f.ackReady ? "THA roi NHAN ACK MOI" : "Cho an toan on dinh 3s");
    }
  }
  if (includesCsv()) printCsvSnapshot(s, f, now, "TELEMETRY");
}
