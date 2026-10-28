#pragma once
#include <cstdint>

// Chân theo Phần F hướng dẫn Nhóm 7; GPIO35 thuộc ADC1, chỉ vào.
namespace Config {
// Dễ đọc khi test tay; chọn Csv để lưu bằng chứng, Both để in cả hai.
enum class SerialLogFormat { Readable, Csv, Both };
constexpr SerialLogFormat kSerialLogFormat = SerialLogFormat::Readable;
constexpr uint8_t kSmokePin = 35;
constexpr uint8_t kLdrPin = 32;
constexpr uint8_t kDoorServoPin = 33;
constexpr uint8_t kDhtPin = 4;
constexpr uint8_t kPumpRelayPin = 26;
constexpr uint8_t kValveRelayPin = 25;
constexpr uint8_t kBuzzerPin = 27;
constexpr uint8_t kRedLedPin = 14;
constexpr uint8_t kGreenLedPin = 13;
constexpr uint8_t kAckPin = 19;
constexpr uint8_t kSdaPin = 21;
constexpr uint8_t kSclPin = 22;
constexpr uint8_t kLcdAddress = 0x27;
// Relay Wokwi khai báo transistor=npn: kích HIGH theo bảng thuộc tính.
// Đèn tải qua COM-NO giúp kiểm chứng cực tính trong mô phỏng.
constexpr uint8_t kRelayOnLevel = 1;
constexpr uint8_t kRelayOffLevel = 0;
constexpr uint8_t kBuzzerChannel = 0;
constexpr uint32_t kBuzzerFrequencyHz = 2000;
// Core2.0.17: kênh0 thuộc group0, kênh8 thuộc group1, timer độc lập.
constexpr uint8_t kServoChannel = 8;
constexpr uint32_t kServoFrequencyHz = 50;
constexpr uint8_t kServoResolutionBits = 16;
constexpr uint32_t kServoMinPulseUs = 500;
constexpr uint32_t kServoMaxPulseUs = 2500;
constexpr uint8_t kDoorClosedAngle = 0;
constexpr uint8_t kDoorOpenAngle = 90;
// Ngưỡng demo ADC, không phải ngưỡng cháy vật lý hay phép đo lux đã hiệu chuẩn.
constexpr int kLdrFireAdc = 500;
constexpr int kLdrClearAdc = 750;
constexpr uint32_t kLdrIntervalMs = 100;
constexpr uint32_t kLdrStaleMs = 500;
constexpr uint32_t kControlIntervalMs = 20;
constexpr uint32_t kAckDebounceMs = 50;
constexpr int kSmokeWarningAdc = 1800;
constexpr int kSmokeDangerAdc = 2800;
constexpr int kSmokeHysteresisAdc = 100;
constexpr float kTemperatureDangerC = 55.0f;
constexpr float kTemperatureClearC = 53.0f;
constexpr float kTemperatureRateDangerCps = 2.0f;
constexpr uint32_t kSuppressionMaxMs = 60000;
constexpr uint32_t kSafeBeforeAckMs = 3000;
constexpr uint32_t kDhtStaleMs = 6500;
constexpr uint32_t kDhtStartupGraceMs = 6500;
constexpr uint32_t kFastStaleMs = 2500;
constexpr uint32_t kSerialBaud = 115200;
constexpr uint32_t kSensorIntervalMs = 1000;
constexpr uint32_t kDhtIntervalMs = 3000;
constexpr uint32_t kDisplayIntervalMs = 500;
// Chỉ giãn snapshot Serial; cảm biến/FSM và EVENT vẫn chạy lịch riêng.
constexpr uint32_t kLogIntervalMs = 3000;
static_assert(kDhtIntervalMs >= 2000, "DHT22 can chu ky toi thieu 2 giay");
static_assert(kLdrFireAdc < kLdrClearAdc, "LDR sang thi ADC giam");
static_assert(kBuzzerChannel / 8 != kServoChannel / 8, "Coi va servo khac nhom LEDC");
}
