#include "outputs.h"
#include <Arduino.h>
#include "config.h"
#include "servo_signal.h"

namespace {
bool buzzerRunning = false;
int doorAngle = -1;
}

void beginOutputs() {
  // Đặt mức tắt trước khi chuyển chân sang OUTPUT, theo cấu hình relay npn.
  for (uint8_t pin : {Config::kPumpRelayPin, Config::kValveRelayPin}) {
    digitalWrite(pin, Config::kRelayOffLevel);
    pinMode(pin, OUTPUT);
  }
  for (uint8_t pin : {Config::kRedLedPin, Config::kGreenLedPin, Config::kBuzzerPin}) {
    digitalWrite(pin, LOW);
    pinMode(pin, OUTPUT);
  }
  // Core Arduino ESP32 2.0.17 đã chốt: dùng LEDC phát xung cho còi thụ động.
  ledcSetup(Config::kBuzzerChannel, Config::kBuzzerFrequencyHz, 8);
  ledcAttachPin(Config::kBuzzerPin, Config::kBuzzerChannel);
  ledcWrite(Config::kBuzzerChannel, 0);
  digitalWrite(Config::kDoorServoPin, LOW);
  pinMode(Config::kDoorServoPin, OUTPUT);
  ledcSetup(Config::kServoChannel, Config::kServoFrequencyHz, Config::kServoResolutionBits);
  ledcAttachPin(Config::kDoorServoPin, Config::kServoChannel);
  ledcWrite(Config::kServoChannel, servoDutyForAngle(Config::kDoorClosedAngle));
  doorAngle = Config::kDoorClosedAngle;
}

void applyOutputs(const SafetySnapshot& safety) {
  digitalWrite(Config::kPumpRelayPin, safety.pumpOn ? Config::kRelayOnLevel : Config::kRelayOffLevel);
  digitalWrite(Config::kValveRelayPin, safety.valveOn ? Config::kRelayOnLevel : Config::kRelayOffLevel);
  digitalWrite(Config::kRedLedPin, safety.redLedOn ? HIGH : LOW);
  digitalWrite(Config::kGreenLedPin, safety.greenLedOn ? HIGH : LOW);
  const int nextAngle = safety.doorOpen ? Config::kDoorOpenAngle : Config::kDoorClosedAngle;
  if (nextAngle != doorAngle) {
    ledcWrite(Config::kServoChannel, servoDutyForAngle(static_cast<uint8_t>(nextAngle)));
    doorAngle = nextAngle;
  }
  if (buzzerRunning != safety.buzzerOn) {
    buzzerRunning = safety.buzzerOn;
    if (buzzerRunning) ledcWriteTone(Config::kBuzzerChannel, Config::kBuzzerFrequencyHz);
    else ledcWrite(Config::kBuzzerChannel, 0);
  }
}

OutputDiagnostics outputDiagnostics() {
  return {ledcReadFreq(Config::kBuzzerChannel), ledcReadFreq(Config::kServoChannel),
      ledcRead(Config::kServoChannel)};
}
