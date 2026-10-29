#pragma once
// Copy secrets.example.h -> secrets.h to override these values (ignored by Git).
#if __has_include("secrets.h")
#include "secrets.h"
#endif
#if __has_include("pccc_runtime_config.h")
#include "pccc_runtime_config.h"
#endif
#ifndef PCCC_NETWORK_ENABLED
#define PCCC_NETWORK_ENABLED 1
#endif
#ifndef PCCC_WIFI_SSID
#define PCCC_WIFI_SSID "Wokwi-GUEST"
#endif
#ifndef PCCC_WIFI_PASSWORD
#define PCCC_WIFI_PASSWORD ""
#endif
#ifndef PCCC_MQTT_URI
#define PCCC_MQTT_URI "mqtt://host.wokwi.internal:1883"
#endif
#ifndef PCCC_TOPIC_PREFIX
#define PCCC_TOPIC_PREFIX "ptit/nhom07/lab-7c49e2"
#endif
#ifndef PCCC_MQTT_USERNAME
#define PCCC_MQTT_USERNAME ""
#endif
#ifndef PCCC_MQTT_PASSWORD
#define PCCC_MQTT_PASSWORD ""
#endif
#ifndef PCCC_NTP_SERVER
#define PCCC_NTP_SERVER "pool.ntp.org"
#endif
namespace NetworkConfig {
constexpr bool kEnabled = PCCC_NETWORK_ENABLED;
constexpr const char* kSsid = PCCC_WIFI_SSID;
constexpr const char* kPassword = PCCC_WIFI_PASSWORD;
constexpr const char* kUri = PCCC_MQTT_URI;
constexpr const char* kUsername = PCCC_MQTT_USERNAME;
constexpr const char* kMqttPassword = PCCC_MQTT_PASSWORD;
constexpr const char* kNtpServer = PCCC_NTP_SERVER;
constexpr const char* kAiTopic = PCCC_TOPIC_PREFIX "/ai/result";
constexpr const char* kTelemetryTopic = PCCC_TOPIC_PREFIX "/device/esp32-01/telemetry";
constexpr const char* kEventTopic = PCCC_TOPIC_PREFIX "/device/esp32-01/event";
constexpr const char* kAvailabilityTopic = PCCC_TOPIC_PREFIX "/device/esp32-01/availability";
}
