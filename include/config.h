#pragma once
#include <Arduino.h>

// Chân theo Phần F hướng dẫn Nhóm 7; GPIO35 thuộc ADC1, chỉ vào.
namespace Config {
// Dễ đọc khi test tay; chọn Csv để lưu bằng chứng, Both để in cả hai.
enum class SerialLogFormat { Readable, Csv, Both };
constexpr SerialLogFormat kSerialLogFormat = SerialLogFormat::Readable;
constexpr uint8_t kSmokePin = 35;
constexpr uint8_t kFlamePin = 18;
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
constexpr uint8_t kFlameActiveLevel = LOW;
// Chỉ dùng cho relay mặc định Wokwi theo phần mô tả operation.
// Phải xác nhận COM-NO/COM-NC trước pha điều khiển tải.
constexpr uint8_t kRelayOffLevel = HIGH;
constexpr uint32_t kSerialBaud = 115200;
constexpr uint32_t kSensorIntervalMs = 1000;
constexpr uint32_t kDhtIntervalMs = 3000;
constexpr uint32_t kDisplayIntervalMs = 500;
constexpr uint32_t kLogIntervalMs = 1000;
static_assert(kDhtIntervalMs >= 2000, "DHT22 can chu ky toi thieu 2 giay");
}
