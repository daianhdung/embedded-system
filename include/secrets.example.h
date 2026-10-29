#pragma once
// Copy to secrets.h (Git ignored). Choose a distinct prefix for each group/run.
#define PCCC_NETWORK_ENABLED 1
#define PCCC_WIFI_SSID "Wokwi-GUEST"
#define PCCC_WIFI_PASSWORD ""
#define PCCC_MQTT_URI "mqtt://host.wokwi.internal:1883"
#define PCCC_TOPIC_PREFIX "ptit/nhom07/replace-with-your-deployment-id"
#define PCCC_MQTT_USERNAME ""
#define PCCC_MQTT_PASSWORD ""
// Lab plaintext broker: publish synthetic data only. Private deployments need
// an authenticated broker and TLS CA verification, not skip-cert validation.
